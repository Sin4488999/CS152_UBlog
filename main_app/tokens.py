from django.contrib.auth.tokens import default_token_generator

# Reusable token generator for email verification links
email_verification_token = default_token_generator