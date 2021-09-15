from django.core.exceptions import ValidationError


def validate_sender(value):
    if len(value) != 34:
        raise ValidationError('sender address is invalid.')
    
def validate_receiver(value):
    if len(value) != 34:
        raise ValidationError('receiver address is invalid.')
