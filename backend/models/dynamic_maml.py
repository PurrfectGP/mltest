import torch
import torch.nn as nn


class DynamicLearner(nn.Module):
    """Meta-learner that generates personalized prediction weights.

    Takes feature vectors and generates user-specific weights for
    preference prediction based on calibration data.
    """

    def __init__(self, in_dim: int = 512, hidden_dim: int = 256, out_dim: int = 1):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim

        # Parameter generator: Takes feature -> Generates weights for the predictor
        self.generator = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, in_dim * out_dim + out_dim)  # Weights + Bias
        )
        # Base predictor (optional usage in 'tuning' mode)
        self.fc = nn.Linear(in_dim, out_dim)

    def gen_forward(self, x: torch.Tensor, mode: str = 'rebirth') -> torch.Tensor:
        """Generate personalized predictions using dynamic weights.

        Args:
            x: Input feature tensor of shape (batch, 512)
            mode: Generation mode ('rebirth' for full weight generation)

        Returns:
            Prediction tensor of shape (batch, 1)
        """
        # Generate weights specific to this input 'x'
        params = self.generator(x)

        # Reshape parameters for inference
        bz = x.size(0)
        weight_num = self.in_dim

        # Split params into weight and bias
        generated_weight = params[:, :weight_num].view(bz, self.in_dim, self.out_dim)
        generated_bias = params[:, weight_num:].view(bz, self.out_dim)

        # Apply generated weights to input x
        # Output = x * generated_weight + generated_bias
        out = torch.bmm(x.unsqueeze(1), generated_weight).squeeze(1) + generated_bias
        return out

    def get_user_weights(self, aggregated_features: torch.Tensor) -> torch.Tensor:
        """Extract the generated weight vector for a user.

        Args:
            aggregated_features: Aggregated calibration features (1, 512)

        Returns:
            Weight vector (512,) representing user's visual preferences
        """
        params = self.generator(aggregated_features)
        weight_num = self.in_dim
        # Return just the weights portion as the user's embedding
        return params[0, :weight_num]
