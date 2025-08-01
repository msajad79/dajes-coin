
def compute_gradient_norm(loss, model):
    grads = torch.autograd.grad(loss, model.parameters(), retain_graph=True, create_graph=True, allow_unused=True)
    # Filter out None gradients and compute norm
    valid_grads = [g for g in grads if g is not None]
    if not valid_grads:
        return torch.tensor(0.0, device=next(model.parameters()).device)
    norm = torch.norm(torch.stack([g.norm() for g in valid_grads]))
    return norm


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
        except RuntimeError:
            # If gradient computation fails, use a small default value
            norms[k] = 1e-8
    
    total = sum(norms.values())
    new_weights = {k: total / v for k, v in norms.items()}  # target: same norm

    # Apply EMA update
    updated_weights = {
        k: alpha * old_weights[k] + (1 - alpha) * new_weights[k] for k in losses
    }
    return updated_weights