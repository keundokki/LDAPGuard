from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.security import get_current_user
from api.models.models import SystemSetting, User
from api.schemas.schemas import SystemSettingResponse, SystemSettingUpdate


# Request models for testing
class EmailTestConfig(BaseModel):
    """Email configuration test request"""
    smtp_server: str
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_encryption: str = "tls"
    from_email: str
    to_email: Optional[str] = None


class S3TestConfig(BaseModel):
    """S3 configuration test request"""
    provider: str = "aws"
    region: str
    bucket: str
    access_key: str
    secret_key: str
    endpoint: Optional[str] = None


class WebhookTestConfig(BaseModel):
    """Webhook configuration test request"""
    webhook_url: str


router = APIRouter(prefix="/settings", tags=["System Settings"])


# Debug endpoint to verify POST routing works
@router.post("/debug-test")
async def debug_test():
    """Debug endpoint to verify POST requests reach this router"""
    return {"status": "ok", "message": "POST method is working on /settings router"}


# Test endpoints MUST come before @router.get("/{key}") to avoid conflicts
@router.post("/test-email", status_code=status.HTTP_200_OK)
async def test_email_configuration(
    email_config: EmailTestConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test email/SMTP configuration. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test email configuration",
        )

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        # Create SMTP connection
        if email_config.smtp_encryption == "ssl":
            server = smtplib.SMTP_SSL(
                email_config.smtp_server, email_config.smtp_port, timeout=10
            )
        else:
            server = smtplib.SMTP(
                email_config.smtp_server, email_config.smtp_port, timeout=10
            )
            if email_config.smtp_encryption == "tls":
                server.starttls()

        # Login if credentials provided
        if email_config.smtp_username and email_config.smtp_password:
            server.login(email_config.smtp_username, email_config.smtp_password)

        # Resolve test recipient
        raw_recipients = email_config.to_email or email_config.from_email
        recipients = [value.strip()
                      for value in raw_recipients.split(",") if value.strip()]
        if not recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test recipient email is required",
            )

        # Send test email
        msg = MIMEMultipart()
        msg["From"] = email_config.from_email
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = "[LDAPGuard] SMTP Configuration Test"

        body = (
            "This is a test email from LDAPGuard to verify SMTP configuration is working correctly."  # noqa: E501
        )
        msg.attach(MIMEText(body, "plain"))

        server.send_message(msg, to_addrs=recipients)
        server.quit()

        return {"status": "success", "message": "SMTP configuration test passed"}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP authentication failed. Check username and password.",
        )
    except smtplib.SMTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SMTP error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test email configuration: {str(e)}",
        )


@router.post("/test-s3", status_code=status.HTTP_200_OK)
async def test_s3_configuration(
    s3_config: S3TestConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test S3 configuration. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test S3 configuration",
        )

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="boto3 library is not installed. Please install it with: pip install boto3",  # noqa: E501
        )

    try:
        # Create S3 client with appropriate configuration
        s3_kwargs = {
            "aws_access_key_id": s3_config.access_key,
            "aws_secret_access_key": s3_config.secret_key,
            "region_name": s3_config.region,
        }

        if s3_config.endpoint:
            s3_kwargs["endpoint_url"] = s3_config.endpoint

        s3_client = boto3.client("s3", **s3_kwargs)

        # Test connection by listing buckets
        response = s3_client.list_buckets()

        # Check if our bucket exists
        bucket_exists = any(
            b["Name"] == s3_config.bucket for b in response.get("Buckets", [])
        )

        if not bucket_exists:
            # Try to create the bucket
            try:
                if s3_config.region == "us-east-1":
                    s3_client.create_bucket(Bucket=s3_config.bucket)
                else:
                    s3_client.create_bucket(
                        Bucket=s3_config.bucket,
                        CreateBucketConfiguration={
                            "LocationConstraint": s3_config.region
                        },
                    )
            except ClientError as e:
                if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
                    pass  # Bucket exists and is ours
                else:
                    raise

        return {
            "status": "success",
            "message": f"S3 connection successful. Bucket '{s3_config.bucket}' is accessible.",  # noqa: E501
            "provider": s3_config.provider,
            "region": s3_config.region,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test S3 configuration: {str(e)}",
        )


@router.post("/test-webhook", status_code=status.HTTP_200_OK)
async def test_webhook_configuration(
    webhook_config: WebhookTestConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test webhook configuration. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test webhook configuration",
        )

    webhook_url = webhook_config.webhook_url.strip()
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is required",
        )

    try:
        import httpx

        base_payload = {
            "event": "webhook.test",
            "message": "LDAPGuard webhook test successful",
            "timestamp": datetime.utcnow().isoformat(),
        }

        payload = {
            **base_payload,
            "text": "LDAPGuard webhook test successful ✅",
            "content": "LDAPGuard webhook test successful ✅",
            "username": "LDAPGuard",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()
            except httpx.ConnectError as conn_err:
                if "CERTIFICATE_VERIFY_FAILED" not in str(conn_err):
                    raise

                async with httpx.AsyncClient(verify=False) as insecure_client:
                    response = await insecure_client.post(
                        webhook_url, json=payload, timeout=10.0
                    )
                    response.raise_for_status()

        return {
            "status": "success",
            "message": "Webhook test delivered successfully",
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook endpoint returned HTTP {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to test webhook configuration: {str(e)}",
        )


@router.get("/", response_model=List[SystemSettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all system settings. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view settings",
        )

    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return settings


@router.get("/{key}", response_model=SystemSettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific setting by key. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view settings",
        )

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found"
        )

    return setting


@router.put("/", response_model=SystemSettingResponse)
async def update_setting(
    setting_data: SystemSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update a system setting. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update settings",
        )

    # Check if setting exists
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting_data.key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        # Update existing setting
        setting.value = setting_data.value
    else:
        # Create new setting
        setting = SystemSetting(key=setting_data.key, value=setting_data.value)
        db.add(setting)

    await db.commit()
    await db.refresh(setting)

    return setting


@router.post("/batch", response_model=List[SystemSettingResponse])
async def batch_update_settings(
    settings: List[SystemSettingUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update multiple settings at once. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update settings",
        )

    updated_settings = []

    for setting_data in settings:
        # Check if setting exists
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == setting_data.key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = setting_data.value
        else:
            setting = SystemSetting(key=setting_data.key, value=setting_data.value)
            db.add(setting)

        updated_settings.append(setting)

    await db.commit()

    # Refresh all settings
    for setting in updated_settings:
        await db.refresh(setting)

    return updated_settings


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a system setting. Admin only."""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete settings",
        )

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found"
        )

    await db.delete(setting)
    await db.commit()

    return None
