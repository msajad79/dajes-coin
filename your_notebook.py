import random

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.integrate import solve_ivp

import torch
import torch.nn as nn
import torch.optim as optim

from sklearn.preprocessing import MinMaxScaler

from ipywidgets import interactive, FloatSlider
from IPython.display import display

from utils import plot_fft

from tqdm import tqdm

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# %%
def Duffing_eq(t, y, delta, alpha, beta, F, omega):
    x, v = y
    dxdt = v
    dvdt = (-delta*v - alpha*x - beta*x**3.0 + F*np.sin(omega*t))
    return [dxdt, dvdt]

# %%
delta = 0.1
alpha = -1.0
beta = 0.25
F = 2.5
omega = 2.0

# %%
y0 = [1.0, 0.0]
num_point = 1000
t_span = (0, 5)
t_eval = np.linspace(t_span[0], t_span[1], num_point)

sol = solve_ivp(Duffing_eq, t_span, y0, t_eval=t_eval, args=(delta, alpha, beta, F, omega))

t = sol.t.astype(np.float32)
x = sol.y[0].astype(np.float32)   
v = sol.y[1].astype(np.float32)

# %%
class MinMaxScalerTorch(MinMaxScaler):
    def __init__(self, feature_range = ..., *, copy = True, clip = False, device=torch.device("cpu")):
        super().__init__(feature_range, copy=copy, clip=clip)
        self.device = device
        
    def fit(self, X, y = None):
        out = super().fit(X, y)
        self.Tmin_ = torch.from_numpy(self.min_).to(self.device)
        self.Tdata_max_ = torch.from_numpy(self.data_max_).to(self.device)
        self.Tdata_min_ = torch.from_numpy(self.data_min_).to(self.device)
        self.Tscale_ = torch.from_numpy(self.scale_).to(self.device)
        return out
    
    def inverse_transform_torch(self, X):
        out = X - self.Tmin_
        out /= self.Tscale_
        return out

# %%
scaler_t = MinMaxScalerTorch((-1.0, 1.0), device=device)
scaler_x = MinMaxScalerTorch((-1.0, 1.0), device=device)
scaler_v = MinMaxScalerTorch((-1.0, 1.0), device=device)

t_star = scaler_t.fit_transform(t.reshape(-1, 1))
x_star = scaler_x.fit_transform(x.reshape(-1, 1))
v_star = scaler_v.fit_transform(v.reshape(-1, 1))

t_star = torch.tensor(t_star).to(device)
x_star = torch.tensor(x_star).to(device)
v_star = torch.tensor(v_star).to(device)


# %%
# Datasets
split_residual = 5
t_star_phy_GvEq = t_star.clone()
target_phy_GvEq = torch.zeros_like(t_star_phy_GvEq).to(device)

num_lbl = 30
idx_lbl = random.sample(range(len(t)), num_lbl)
t_star_lbl = t_star.clone()[idx_lbl].to(device)
target_lbl = x_star.clone()[idx_lbl].to(device)


# required grad
t_star_phy_GvEq.requires_grad = True

# %%
class Cosine(nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def forward(self, input):
        x = torch.zeros_like(input)
        for i in range(input.shape[1]):
            x[:,i] = torch.cos((i+1)*torch.pi*input[:,i])
        return x

class Sine(nn.Module):

    def forward(self, input):
        return torch.sin(input)

class FourierFeatureEmbedding(nn.Module):
    def __init__(self, in_dim=1, num_frequencies=32, sigma=10.0):
        super().__init__()
        self.B = nn.Parameter(
            torch.randn(num_frequencies, in_dim) * sigma, requires_grad=True
        )

    def forward(self, x):
        # x: shape (batch_size, in_dim)
        x_proj = 2 * torch.pi * x @ self.B.T  # (batch_size, num_frequencies)
        return torch.cat([torch.sin(x_proj), torch.cos(x_proj)], dim=-1)  # shape (batch, 2 * num_frequencies)
    
class MLP(nn.Module):
    def __init__(self, layers_size):
        super(MLP, self).__init__()

        self.embedding = FourierFeatureEmbedding()

        self.activation = nn.Tanh()

        layers = []

        for in_size, out_size in zip(layers_size[:-1], layers_size[1:]):
            linear = nn.Linear(in_size, out_size)
            # Xavier Glorot initialization
            nn.init.xavier_uniform_(linear.weight)
            nn.init.zeros_(linear.bias)
            layers.append(linear)
            layers.append(self.activation)
        
        self.fc = nn.Sequential(
            *layers[:-1]    
        )
        
    def forward(self, t):
        embed = self.embedding(t)
        y = self.fc(embed)
        return y

# %%
model = MLP([64, 128, 128, 128, 1])
model.to(device)

optimizer = optim.Adam(model.parameters(), lr=0.0001)

# %%
optimizer = optim.Adam(model.parameters(), lr=0.00001)

# %%
def compute_causal_weights(residual_losses, epsilon=1.0):
    """
    residual_losses: list of tensors, each L_r^(i) for time segment i
    returns: list of weights w_i
    """
    weights = [torch.tensor(1.0, device=residual_losses[0].device)]
    cumulative = 0.0
    for i in range(1, len(residual_losses)):
        cumulative += residual_losses[i-1].detach()  # detach to avoid gradient flow
        wi = torch.exp(-epsilon * cumulative)
        weights.append(wi)
    return weights

# %%
def compute_gradient_norm(loss, model):
    """
    Compute gradient norm with proper handling of unused parameters
    """
    try:
        grads = torch.autograd.grad(
            loss, 
            model.parameters(), 
            retain_graph=True, 
            create_graph=True, 
            allow_unused=True
        )
        # Filter out None gradients and compute norm
        valid_grads = [g for g in grads if g is not None]
        if not valid_grads:
            return torch.tensor(0.0, device=next(model.parameters()).device)
        norm = torch.norm(torch.stack([g.norm() for g in valid_grads]))
        return norm
    except RuntimeError as e:
        # If gradient computation fails, return a small default value
        return torch.tensor(1e-8, device=next(model.parameters()).device)


@torch.no_grad()
def update_loss_weights_gradient_based(losses, model, old_weights, alpha=0.9):
    """
    losses: dict {name: loss_value} like {'ic': L_ic, 'bc': L_bc, 'r': L_r}
    model: the PINN model
    old_weights: dict {name: lambda_value}, initial weights
    alpha: momentum factor for exponential moving average
    returns: updated_weights dict
    """
    norms = {}
    for k, loss in losses.items():
        try:
            norm = compute_gradient_norm(loss, model).item()
            norms[k] = max(norm, 1e-8)  # Avoid division by zero
        except (RuntimeError, AttributeError):
            # If gradient computation fails, use a small default value
            norms[k] = 1e-8
    
    total = sum(norms.values())
    if total == 0:
        total = 1e-8
    
    new_weights = {k: total / v for k, v in norms.items()}  # target: same norm

    # Apply EMA update
    updated_weights = {
        k: alpha * old_weights[k] + (1 - alpha) * new_weights[k] for k in losses
    }
    return updated_weights

# %%
def closure():
    global loss_weights
    optimizer.zero_grad()

    x_star_pred_phy_GvEq = model(t_star_phy_GvEq)
    x_star_pred_lbl = model(t_star_lbl)

    x_pred_phy_GvEq = (x_star_pred_phy_GvEq-scaler_x.Tmin_)/scaler_x.Tscale_ #scaler_x.inverse_transform_torch(x_star_pred_phy_GvEq)
    t_phy_GvEq = scaler_t.inverse_transform_torch(t_star_phy_GvEq)
    
    # grads 
    dxdt_star_GvEq, = torch.autograd.grad(x_pred_phy_GvEq[:,0], t_star_phy_GvEq, torch.ones_like(x_pred_phy_GvEq[:,0]), create_graph=True)[0].unbind(dim=1)
    dxdt_GvEq = dxdt_star_GvEq * scaler_t.Tscale_
    d2xdtdt_star_GvEq, = torch.autograd.grad(dxdt_GvEq, t_star_phy_GvEq, torch.ones_like(dxdt_GvEq), create_graph=True)[0].unbind(dim=1)
    d2xdt2_GvEq = d2xdtdt_star_GvEq * scaler_x.Tscale_
    
    # Residual of GvEq
    R_GvEq = d2xdt2_GvEq + delta*dxdt_GvEq + alpha*x_pred_phy_GvEq.squeeze(1) - F*torch.sin(omega*t_phy_GvEq.squeeze(1))
    # physics losses
    losses_phy_GvEq = []
    for R_GvEq_part, targets_phy_GvEq_part in zip(torch.split(R_GvEq, len(R_GvEq)//split_residual), torch.split(target_phy_GvEq, len(R_GvEq)//split_residual)):
        losses_phy_GvEq.append(nn.functional.mse_loss(R_GvEq_part, targets_phy_GvEq_part.squeeze(1)))
    weights = compute_causal_weights(losses_phy_GvEq)
    loss_phy_GvEq = torch.stack([w * l for w, l in zip(weights, losses_phy_GvEq)]).mean()

    # ICs
    loss_IC_x = nn.functional.mse_loss(x_pred_phy_GvEq[0], torch.tensor([1.0]).to(device))
    loss_IC_v = nn.functional.mse_loss(dxdt_GvEq[0], torch.tensor([0.0]).to(device))

    # labeled loss
    loss_lbl = nn.functional.mse_loss(x_star_pred_lbl, target_lbl)

    losses_info = {
        'ic v': loss_IC_v,
        'ic x': loss_IC_x,
        'pde': loss_phy_GvEq,
        'lbl':loss_lbl
    }

    loss_weights = update_loss_weights_gradient_based(losses_info, model, loss_weights, alpha=0.9)
    # loss_weights = update_loss_weights_ntk_based(losses, model, loss_weights, alpha=0.9)

    total_loss = sum(loss_weights[k] * losses_info[k] for k in losses_info)
    
    total_loss.backward()

    return total_loss

# %%
model.train()

loss_weights = {
    'ic v': 1.0,
    'ic x': 1.0,
    'pde': 1.0,
    'lbl':1.0
}

for i in (p_bar:=tqdm(range(5000))):
    loss = optimizer.step(closure)
    p_bar.set_description(f"loss = {loss.item()}")

# %%
model.eval()

x_star_val_pred_phy = model(t_star_phy_GvEq)
x_star_val_pred_lbl = model(t_star_lbl)

x_val_pred_phy = scaler_x.inverse_transform_torch(x_star_val_pred_phy)

# grads
dxdt_star_GvEq, = torch.autograd.grad(x_val_pred_phy[:,0], t_star_phy_GvEq, torch.ones_like(x_val_pred_phy[:,0]), create_graph=True)[0].unbind(dim=1)
dxdt_GvEq = dxdt_star_GvEq * scaler_t.Tscale_
# d2xdtdt_star_GvEq, = torch.autograd.grad(dxdt_GvEq, t_star_phy_GvEq, torch.ones_like(dxdt_GvEq), create_graph=True)[0].unbind(dim=1)
# d2xdt2_GvEq = d2xdtdt_star_GvEq * scaler_x.Tscale_