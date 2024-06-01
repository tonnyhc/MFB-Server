from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions
from django.core.exceptions import ValidationError
from rest_framework import serializers

from server.authentication.tasks import send_confirmation_code_for_register

# from server.authentication.utils import send_confirmation_code_for_register

UserModel = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = UserModel
        fields = ('__all__')

    def validate(self, attrs):
        # email_or_username = attrs.get('email_or_username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(request=self.context['request'], email=email, password=password)

        # if "@" in email_or_username:
        #     user = authenticate(request=self.context['request'], email=email_or_username, password=password)
        # else:
        #     user = authenticate(request=self.context['request'], username=email_or_username, password=password)

        if not user:
            raise serializers.ValidationError('Invalid email/username or password')

        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('email', 'username', 'password')

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']

        user = UserModel.objects.create_user(
            email=email.lower(),
            username=username.lower(),
            password=password,
        )

        # send_confirmation_code_for_register.delay(user.pk)

        return user

    def validate(self, data):
        user = UserModel
        password = data.get('password')
        errors = {}
        try:
            password_validation.validate_password(password, user)
        except exceptions.ValidationError as e:
            errors['password'] = list(e.messages)
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(data)

    def validate_email(self, value):
        lowercased_email = value.lower()
        existing_user = UserModel.objects.filter(email__iexact=lowercased_email)
        if existing_user.exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return lowercased_email

    def validate_username(self, value):
        lowercased_username = value.lower()
        existing_user = UserModel.objects.filter(username__iexact=lowercased_username)
        if existing_user.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return lowercased_username

    def to_representation(self, instance):
        user_representation = super().to_representation(instance)
        user_representation.pop('password')
        return user_representation


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ConfirmVerificationCodeForPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    re_pass = serializers.CharField(required=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        return value

    def validate(self, data):
        password = data.get('password')
        re_pass = data.get('re_pass')
        if password and re_pass and password != re_pass:
            raise serializers.ValidationError("Passwords do not match.")
        return data
