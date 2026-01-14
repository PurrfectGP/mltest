import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid

import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

from models import ResNetBackbone, DynamicLearner


class VisualService:
    """Service for visual calibration using MetaFBP algorithm.

    MetaFBP Process:
    1. ResNetBackbone extracts 512-dim feature vectors from face images
    2. User rates images (1-5 stars) during calibration
    3. Features are weighted by ratings and aggregated
    4. DynamicLearner generates personalized weight vector from aggregated features
    5. Result is saved as p1_visual_vector.json

    The DynamicLearner acts as a "parameter generator" - it takes the user's
    preference signal (aggregated features) and outputs a personalized weight
    vector that represents what the user finds attractive.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to avoid reloading models."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        data_dir: str = "/app/data",
        device: Optional[str] = None,
        backbone_weights: Optional[str] = None,
        learner_weights: Optional[str] = None
    ):
        """Initialize the VisualService.

        Args:
            data_dir: Base directory for data storage
            device: Torch device ('cuda' or 'cpu')
            backbone_weights: Path to pre-trained backbone weights
            learner_weights: Path to pre-trained learner weights
        """
        if self._initialized:
            return

        self.data_dir = Path(data_dir)
        self.profiles_dir = self.data_dir / "profiles"
        self.calibration_dir = self.data_dir / "global_calibration"

        # Ensure directories exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_dir.mkdir(parents=True, exist_ok=True)

        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Initialize models
        print(f"Initializing MetaFBP models on {self.device}...")
        self.backbone = ResNetBackbone(pretrained=True).to(self.device)
        self.learner = DynamicLearner(in_dim=512, hidden_dim=256, out_dim=1).to(self.device)

        # Load custom weights if provided
        if backbone_weights and os.path.exists(backbone_weights):
            self.backbone.load_state_dict(torch.load(backbone_weights, map_location=self.device))
        if learner_weights and os.path.exists(learner_weights):
            self.learner.load_state_dict(torch.load(learner_weights, map_location=self.device))

        # Set to evaluation mode (inference only - no training)
        self.backbone.eval()
        self.learner.eval()

        # Image preprocessing pipeline (ImageNet normalization)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        self._initialized = True
        print("MetaFBP models initialized successfully")

    def extract_features(self, image_paths: List[str]) -> torch.Tensor:
        """Extract 512-dim feature vectors from images using ResNetBackbone.

        Args:
            image_paths: List of paths to image files

        Returns:
            Feature tensor of shape (batch, 512)
        """
        images = []
        for path in image_paths:
            img = Image.open(path).convert("RGB")
            img_tensor = self.transform(img)
            images.append(img_tensor)

        batch = torch.stack(images).to(self.device)

        with torch.no_grad():
            features = self.backbone(batch)

        return features

    def extract_single_feature(self, image_path: str) -> torch.Tensor:
        """Extract feature vector from a single image.

        Args:
            image_path: Path to image file

        Returns:
            Feature tensor of shape (512,)
        """
        return self.extract_features([image_path])[0]

    def _generate_demo_features(self, image_id: str, rating: int) -> torch.Tensor:
        """Generate deterministic demo features when no real images exist.

        Uses image_id as seed for reproducibility, and rating influences
        the feature distribution to simulate preference patterns.

        Args:
            image_id: Image identifier (used as seed)
            rating: User rating 1-5

        Returns:
            Synthetic feature tensor of shape (512,)
        """
        # Create deterministic seed from image_id
        seed = hash(image_id) % (2**32)
        torch.manual_seed(seed)

        # Generate base features
        features = torch.randn(512, device=self.device)

        # Normalize to unit sphere
        features = F.normalize(features, dim=0)

        return features

    def calibrate_user(
        self,
        user_id: str,
        ratings: Dict[str, int],
        gender: Optional[str] = None,
        preference_target: Optional[str] = None
    ) -> Dict:
        """Calibrate user preferences using MetaFBP algorithm.

        MetaFBP Calibration Process:
        1. Extract features from each rated image (or generate demo features)
        2. Weight features by user ratings (1-5 stars normalized to 0-1)
        3. Aggregate weighted features into a single preference vector
        4. Pass through DynamicLearner to generate personalized embedding
        5. Compute ideal_vector as centroid of highly-rated images
        6. Save everything to p1_visual_vector.json

        Args:
            user_id: Unique user identifier
            ratings: Dict mapping image_id to rating (1-5 stars)
            gender: User's gender
            preference_target: Gender preference for matching

        Returns:
            Generated p1_visual_vector data structure
        """
        if not ratings:
            raise ValueError("No ratings provided for calibration")

        # Collect features and ratings
        features_list = []
        ratings_list = []
        liked_features = []  # Ratings >= 4
        disliked_features = []  # Ratings <= 2

        for image_id, rating in ratings.items():
            # Try to load real image
            image_path = self.calibration_dir / f"{image_id}.jpg"
            if not image_path.exists():
                image_path = self.calibration_dir / f"{image_id}.png"

            if image_path.exists():
                # Real image exists - extract actual features
                feature = self.extract_single_feature(str(image_path))
            else:
                # Demo mode - generate synthetic features
                feature = self._generate_demo_features(image_id, rating)

            features_list.append(feature)
            ratings_list.append(rating)

            # Categorize by rating for preference model
            if rating >= 4:
                liked_features.append(feature)
            elif rating <= 2:
                disliked_features.append(feature)

        if not features_list:
            raise ValueError("No valid ratings for calibration")

        # Stack features into batch tensor
        features = torch.stack(features_list)  # Shape: (N, 512)
        ratings_tensor = torch.tensor(ratings_list, dtype=torch.float32, device=self.device)

        # Normalize ratings to [0, 1] weights
        # Rating 1 -> weight 0.0, Rating 5 -> weight 1.0
        weights = (ratings_tensor - 1) / 4.0

        # Compute weighted average of features
        # This represents the user's aggregate preference signal
        weights_expanded = weights.unsqueeze(1)  # Shape: (N, 1)
        weighted_features = features * weights_expanded  # Shape: (N, 512)
        aggregated_features = weighted_features.sum(dim=0, keepdim=True) / (weights.sum() + 1e-8)  # Shape: (1, 512)

        # Generate user-specific embedding using DynamicLearner
        # The learner takes the preference signal and outputs personalized weights
        with torch.no_grad():
            user_embedding = self.learner.get_user_weights(aggregated_features)

        # Compute ideal_vector as centroid of highly-rated (liked) images
        ideal_vector = None
        if liked_features:
            liked_stack = torch.stack(liked_features)
            ideal_vector = liked_stack.mean(dim=0)

        # Calculate calibration confidence based on rating variance
        # High variance = decisive preferences = high confidence
        calibration_confidence = self._calculate_confidence(ratings_list)

        # Detect attraction triggers (placeholder for trait classifier)
        attraction_triggers = self._detect_triggers(liked_features, disliked_features)

        # Build the p1_visual_vector structure per spec
        vector_data = {
            "meta": {
                "user_id": user_id,
                "gender": gender or "unspecified",
                "preference_target": preference_target or "unspecified",
                "calibration_timestamp": datetime.utcnow().isoformat() + "Z",
                "images_rated": len(ratings)
            },
            "self_analysis": {
                "embedding_vector": user_embedding.cpu().tolist(),
                "detected_traits": {
                    "facial_landmarks": ["placeholder"],
                    "style_presentation": ["placeholder"],
                    "vibe_tags": ["placeholder"]
                }
            },
            "preference_model": {
                "ideal_vector": ideal_vector.cpu().tolist() if ideal_vector is not None else [],
                "attraction_triggers": attraction_triggers,
                "calibration_confidence": calibration_confidence
            }
        }

        # Save the vector to user's profile directory
        self.save_vector(user_id, vector_data)

        return vector_data

    def _calculate_confidence(self, ratings: List[int]) -> float:
        """Calculate calibration confidence from rating distribution.

        Higher variance in ratings indicates more decisive preferences,
        which translates to higher confidence in the calibration.
        """
        if len(ratings) < 3:
            return 0.5

        import statistics
        variance = statistics.variance(ratings)
        # Normalize: max variance for 1-5 scale is ~4
        confidence = min(variance / 2.0, 1.0)
        return round(confidence, 2)

    def _detect_triggers(
        self,
        liked_features: List[torch.Tensor],
        disliked_features: List[torch.Tensor]
    ) -> Dict:
        """Detect attraction triggers from liked/disliked patterns.

        In production, this would use a trained trait classifier.
        For MVP, returns placeholder structure.
        """
        return {
            "mandatory_traits": ["placeholder_positive_trait"],
            "negative_traits": ["placeholder_negative_trait"]
        }

    def save_vector(self, user_id: str, vector_data: Dict) -> Path:
        """Save the visual vector to the user's profile directory.

        Args:
            user_id: Unique user identifier
            vector_data: The p1_visual_vector data structure

        Returns:
            Path to the saved file
        """
        user_dir = self.profiles_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        vector_path = user_dir / "p1_visual_vector.json"
        with open(vector_path, "w") as f:
            json.dump(vector_data, f, indent=2)

        print(f"Saved visual vector for user {user_id} to {vector_path}")
        return vector_path

    def load_vector(self, user_id: str) -> Optional[Dict]:
        """Load existing visual vector for a user.

        Args:
            user_id: Unique user identifier

        Returns:
            Vector data or None if not found
        """
        vector_path = self.profiles_dir / user_id / "p1_visual_vector.json"
        if not vector_path.exists():
            return None

        with open(vector_path, "r") as f:
            return json.load(f)

    def get_calibration_images(self, count: int = 20) -> List[Dict]:
        """Get a list of calibration images for rating.

        If no real images exist, returns demo placeholder references.

        Args:
            count: Number of images to return

        Returns:
            List of image metadata dicts
        """
        images = []

        # Check for real images first
        if self.calibration_dir.exists():
            real_images = list(self.calibration_dir.glob("*.[jp][pn][g]"))
            for img_path in sorted(real_images)[:count]:
                images.append({
                    "id": img_path.stem,
                    "filename": img_path.name,
                    "url": f"/api/calibration/images/{img_path.name}"
                })

        # If no real images, provide demo placeholders
        if not images:
            for i in range(1, count + 1):
                images.append({
                    "id": f"demo_{i}",
                    "filename": f"demo_{i}.jpg",
                    "url": f"https://picsum.photos/seed/{i}/400/500"  # Random placeholder
                })

        return images
