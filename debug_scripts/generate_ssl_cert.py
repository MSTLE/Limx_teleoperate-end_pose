#!/usr/bin/env python3
"""
生成自签名SSL证书用于HTTPS连接
WebXR需要HTTPS才能访问设备传感器
"""

from OpenSSL import crypto
import os

def generate_self_signed_cert():
    """生成自签名证书"""
    
    # 创建密钥对
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # 创建自签名证书
    cert = crypto.X509()
    cert.get_subject().C = "CN"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Organization"
    cert.get_subject().OU = "Organizational Unit"
    cert.get_subject().CN = "localhost"
    
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 有效期1年
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # 保存证书和密钥
    cert_path = os.path.join(os.path.dirname(__file__), "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "key.pem")
    
    with open(cert_path, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    with open(key_path, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
    
    print("✅ SSL证书已生成:")
    print(f"   证书: {cert_path}")
    print(f"   密钥: {key_path}")
    print("\n⚠️  这是自签名证书，浏览器会显示安全警告")
    print("   在Quest浏览器中需要点击'继续访问'或'接受风险'")

if __name__ == "__main__":
    print("="*60)
    print("生成SSL证书")
    print("="*60)
    
    try:
        generate_self_signed_cert()
    except ImportError:
        print("\n❌ 缺少pyOpenSSL库")
        print("   安装: pip install pyOpenSSL")
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")

