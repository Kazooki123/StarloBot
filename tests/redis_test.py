import redis
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_PASS = os.getenv('REDIS_PASSWORD')
HOST = os.getenv('UPSTASH_HOST')

r = redis.Redis(
  host=HOST,
  port=6379,
  password=REDIS_PASS,
  ssl=True
)

r.set('elastic', 'girl')
print(r.get('elastic'))