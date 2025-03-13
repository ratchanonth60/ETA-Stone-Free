CACHES = {
    # "default": {
    #     "BACKEND": "django.core.cache.backends.redis.RedisCache",
    #     "LOCATION": [
    #         "redis://127.0.0.1:6379",  # leader
    #         "redis://127.0.0.1:6378",  # read-replica 1
    #         "redis://127.0.0.1:6377",  # read-replica 2
    #     ],
    # },
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    },
    "redis": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis/1",  # URL ของ Redis
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_FUNCTION": "django_tenants.cache.make_key",
        "REVERSE_KEY_FUNCTION": "django_tenants.cache.reverse_key",
    },
}

"""
from django.core.cache import cache  # ใช้ cache ประเภท "default"
from django.core.cache import caches

# ใช้งาน DatabaseCache
db_cache = caches['db']
db_cache.set('my_key', 'my_value', 300)
value = db_cache.get('my_key')

# ใช้งาน RedisCache
redis_cache = caches['redis']
redis_cache.set('my_redis_key', 'my_redis_value', 300)
redis_value = redis_cache.get('my_redis_key')
"""
