import redis
import ssl
import certifi

url = "rediss://default:gQAAAAAAAz0iAAIgcDFjYzg2ZGMyYjRkYjQ0M2I3OWYwYmIyMjAwYmY2ODMzNA@allowed-deer-212258.upstash.io:6379/0"

try:
    r = redis.from_url(url, ssl_cert_reqs=ssl.CERT_REQUIRED, ssl_ca_certs=certifi.where())
    r.ping()
    print("Connection successful with 'default' username!")
except redis.exceptions.AuthenticationError as e:
    print(f"Auth error with 'default': {e}")
    try:
        # Try without username
        url_no_user = "rediss://:gQAAAAAAAz0iAAIgcDFjYzg2ZGMyYjRkYjQ0M2I3OWYwYmIyMjAwYmY2ODMzNA@allowed-deer-212258.upstash.io:6379/0"
        r2 = redis.from_url(url_no_user, ssl_cert_reqs=ssl.CERT_REQUIRED, ssl_ca_certs=certifi.where())
        r2.ping()
        print("Connection successful WITHOUT username!")
    except Exception as e2:
        print(f"Failed again: {e2}")
except Exception as e:
    print(f"Other error: {e}")
