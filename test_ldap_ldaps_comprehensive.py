#!/usr/bin/env python
"""Test LDAP and LDAPS connectivity for LDAPGuard."""
import ldap
import socket

def test_ldap_ldaps():
    """Test both LDAP and LDAPS connections."""
    
    test_cases = [
        {
            'name': 'LDAP (unencrypted)',
            'url': 'ldap://localhost:3389',
            'bind_dn': 'cn=admin,dc=example,dc=com',
            'password': 'admin_password',
        },
        {
            'name': 'LDAPS (encrypted) - localhost',
            'url': 'ldaps://localhost:6363',
            'bind_dn': 'cn=admin,dc=example,dc=com',
            'password': 'admin_password',
            'tls_options': {
                ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
                ldap.OPT_X_TLS_NEWCTX: 0,
            }
        },
        {
            'name': 'LDAPS (encrypted) - 127.0.0.1',
            'url': 'ldaps://127.0.0.1:6363',
            'bind_dn': 'cn=admin,dc=example,dc=com',
            'password': 'admin_password',
            'tls_options': {
                ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
                ldap.OPT_X_TLS_NEWCTX: 0,
            }
        },
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print('='*60)
        
        # Apply TLS options if needed
        if 'tls_options' in test:
            for opt, val in test['tls_options'].items():
                ldap.set_option(opt, val)
        
        try:
            # Initialize connection
            conn = ldap.initialize(test['url'])
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 5)
            
            # Bind
            conn.simple_bind_s(test['bind_dn'], test['password'])
            print(f"✅ Authentication: SUCCESS")
            
            # Search
            result = conn.search_ext_s(
                'dc=example,dc=com',
                ldap.SCOPE_SUBTREE,
                '(objectClass=*)',
                None,
                0, None, None, -1, 0
            )
            print(f"✅ Search: SUCCESS - found {len(result)} entries")
            
            conn.unbind_s()
            print(f"✅ Overall: WORKING ✅")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")

if __name__ == '__main__':
    test_ldap_ldaps()
