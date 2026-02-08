#!/usr/bin/env python
import ldap
import socket

hosts_to_test = [
    'localhost:6363',
    '127.0.0.1:6363',
    'host.containers.internal:6363',
]

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

for host_port in hosts_to_test:
    host, port = host_port.rsplit(':', 1)
    print(f"\nTesting {host_port}...")
    
    # Test socket first
    try:
        sock = socket.create_connection((host, int(port)), timeout=5)
        sock.close()
        print(f"  ✅ Socket connection works")
    except Exception as e:
        print(f"  ❌ Socket connection failed: {e}")
        continue
    
    # Test LDAPS
    try:
        conn = ldap.initialize(f'ldaps://{host_port}')
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
        
        conn.simple_bind_s('cn=admin,dc=example,dc=com', 'admin_password')
        print(f"  ✅ LDAPS bind works!")
        conn.unbind_s()
    except Exception as e:
        print(f"  ❌ LDAPS bind failed: {e}")
