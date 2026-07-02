"""
AES加密工具 - 用于敏感配置项（如API Key）的加密存储
"""
import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


# 加密密钥（32字节，从SECRET_KEY派生）
def _get_encryption_key():
    """从Flask SECRET_KEY派生32字节AES密钥"""
    from flask import current_app
    secret = current_app.config.get('SECRET_KEY', 'default-secret-key')
    return hashlib.sha256(secret.encode('utf-8')).digest()


def encrypt(plaintext: str) -> str:
    """
    AES-256-CBC加密
    返回 base64(IV + ciphertext) 编码的字符串
    """
    if not plaintext:
        return ''

    key = _get_encryption_key()
    iv = os.urandom(16)

    # PKCS7填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # IV + 密文
    return base64.b64encode(iv + ciphertext).decode('utf-8')


def decrypt(encrypted_text: str) -> str:
    """
    AES-256-CBC解密
    从 base64(IV + ciphertext) 解码并解密
    """
    if not encrypted_text:
        return ''

    try:
        key = _get_encryption_key()
        raw = base64.b64decode(encrypted_text.encode('utf-8'))

        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # 移除PKCS7填充
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()

        return plaintext.decode('utf-8')
    except Exception:
        # 解密失败（可能是旧数据未加密），返回原值
        return encrypted_text
