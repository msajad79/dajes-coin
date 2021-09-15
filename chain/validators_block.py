from django.core.exceptions import ValidationError



def validate_hash_block(hash_block):
    from chain.models import Block
    difficulty = Block.get_difficulty()
    if hash_block[:difficulty] != ("0"*difficulty):
        raise ValidationError("hash block is invalid.")

def validate_prev_block(prev_block):
    from chain.models import Block
    block:Block = Block.objects.all().order_by('-id').first()
    if block is None:
        if not prev_block is None:
            raise ValidationError("prev_block is invalid")
    else:
        if prev_block.id != block.id:
            raise ValidationError("prev block is invalid")

def validate_difficulty(value):
    from chain.models import Block
    if Block.get_difficulty() != value:
        raise ValidationError('difficulty level is invalid.')

def validate_timestamp(value):
    from chain.models import Block
    block = Block.objects.all().order_by('-id').first()
    if block is not None and block.timestamp >= value:
        raise ValidationError("timestamp is invalid")
