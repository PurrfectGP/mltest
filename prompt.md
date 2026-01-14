=============================================================================== SECTION A: MANDATORY DEVELOPMENT REGIMEN

STEP 1: FIND (Discovery)

Confirm understanding: Build a PWA where users:

Sign up & answer "Fixed Five" psychometric questions.

Rate a sequence of stock images (Visual Calibration).

Backend uses MetaFBP logic to generate a personalized p1_visual_vector.json.

ASK clarifying questions if ambiguity exists.

STEP 2: VERIFY (Research)

Use the embedded code below as the source of truth for the ML logic.

Reference the attached Harmonia V3_ Master Technical Specification.docx for data schemas.

STEP 3: CATEGORIZE

Architecture: Moderate (FastAPI Backend + React/Vite Frontend).

STEP 4: PLAN

Present EXACTLY 5 plans. One must specifically address "Service-Based Refactoring" of the embedded MetaFBP code.

STEP 5: PRESENT

Summarize and ask for approval.

STEP 6: EXECUTE

Implement ONLY the approved plan.

=============================================================================== SECTION B: CONTEXT & EMBEDDED CODE

Project: Harmonia Phase 1 Testing App.
Task: Refactor the provided Research Code (MetaFBP) into a VisualService class wrapped by a FastAPI app and React frontend.

EMBEDDED CODE 1: The Backbone (model/resnet.py reference)
Context: This defines the feature extractor. In the app, we will load a pre-trained version.

import torch
import torch.nn as nn
from torchvision.models import resnet18

class ResNetBackbone(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        # Use standard torchvision resnet18, remove fc layer
        base = resnet18(pretrained=pretrained)
        self.features = nn.Sequential(*list(base.children())[:-1])
        self.fea_dim = 512

    def forward(self, x):
        x = self.features(x)
        return x.view(x.size(0), -1)


EMBEDDED CODE 2: The Meta-Learner (model/dynamic_maml.py reference)
Context: This is the core logic we need to refactor. The DynamicLearner generates weights based on input features.

import torch
import torch.nn as nn
import torch.nn.functional as F

class DynamicLearner(nn.Module):
    def __init__(self, in_dim=512, hidden_dim=256, out_dim=1):
        super().__init__()
        # Parameter generator: Takes feature -> Generates weights for the predictor
        self.generator = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, in_dim * out_dim + out_dim) # Weights + Bias
        )
        self.fc = nn.Linear(in_dim, out_dim) # Base predictor (optional usage in 'tuning' mode)

    def gen_forward(self, x, mode='rebirth'):
        # Generate weights specific to this input 'x'
        params = self.generator(x)
        
        # Reshape parameters (Simplified for inference context)
        # In 'rebirth' mode, we generate new weights entirely.
        bz = x.size(0)
        weight_num = 512 # in_dim
        
        # Split params into weight and bias
        generated_weight = params[:, :weight_num].view(bz, 512, 1)
        generated_bias = params[:, weight_num:].view(bz, 1)
        
        # Apply generated weights to input x
        # Output = x * generated_weight + generated_bias
        out = torch.bmm(x.unsqueeze(1), generated_weight).squeeze(2) + generated_bias
        return out


=============================================================================== SECTION E: HARD CONSTRAINTS

MUST NOT DO:
X Do not use the training loops (meta_train) found in the original repo. We are doing inference (calibration) only.
X Do not hallucinate new psychometric questions.

MUST DO:

Implement the "Fixed Five" questions:

Dinner Check

Tech Meltdown

Found Wallet

Restaurant Choice

Spontaneous Trip

Create a VisualService that initializes the ResNetBackbone and DynamicLearner.

VisualService.calibrate_user(ratings) must:

Extract features from rated images using ResNetBackbone.

Use DynamicLearner to generate the user's specific weight vector.

Save this vector to p1_visual_vector.json.

Generate p1_visual_vector.json exactly matching the Spec schema.

Frontend: 1-5 Star Rating System.

=============================================================================== SECTION F: TECHNICAL SPECIFICATIONS

Data Schema (p1_visual_vector.json):

{
  "meta": { "user_id": "uuid_1" },
  "self_analysis": {
    "embedding_vector": [0.123, -0.45, ...], 
    "detected_traits": {
      "facial_landmarks": ["placeholder"],
      "vibe_tags": ["placeholder"]
    }
  }
}
