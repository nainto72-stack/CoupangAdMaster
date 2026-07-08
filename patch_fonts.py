import re
import platform

def patch(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace rcParams
    content = content.replace(
        "plt.rcParams['font.family'] = 'Malgun Gothic'",
        "plt.rcParams['font.family'] = 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'"
    )

    # 2. Replace fontdict={'family': 'Malgun Gothic'}
    content = content.replace(
        "'family': 'Malgun Gothic'",
        "'family': 'NanumGothic' if __import__('platform').system() == 'Linux' else 'Malgun Gothic'"
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

patch('web_app.py')
patch('app.py')
print("Patched fonts!")
