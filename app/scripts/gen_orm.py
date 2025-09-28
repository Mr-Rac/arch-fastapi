import os
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

_URL = (
    f"mysql+pymysql://"
    f"{os.getenv('MYSQL_USERNAME')}:{os.getenv('MYSQL_PASSWORD')}@"
    f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}"
)
_DB = [
    "auth",
]
_OUTPUT_FILE = "../models/{}.py"


def gen():
    try:
        for db in _DB:
            file = _OUTPUT_FILE.format(db)
            subprocess.run([
                sys.executable,
                "-m",
                "sqlacodegen",
                f"{_URL}/{db}",
                "--outfile", file,
            ], check=True)
            print(f"数据库「{db}」ORM生成成功，路径: {file}")
    except subprocess.CalledProcessError as e:
        print(f"ORM生成失败: {e}")


if __name__ == "__main__":
    gen()
