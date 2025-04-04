import matplotlib.font_manager
import pandas as pd
import sys

print(f"Python version: {sys.version}")
print(f"Matplotlib version: {matplotlib.__version__}")
print(f"Pandas version: {pd.__version__}")

print("\nAttempting to find system fonts...")
# 获取所有可用字体列表
try:
    font_list = matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    print(f"Found {len(font_list)} font files.")
except Exception as e:
    print(f"Error calling findSystemFonts: {e}")
    font_list = []

# 提取字体名称
font_names = []
if font_list:
    print("Extracting font names...")
    for i, font_path in enumerate(font_list):
        try:
            font_prop = matplotlib.font_manager.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            font_names.append(font_name)
            # Print progress occasionally for long lists
            # if (i + 1) % 100 == 0:
            #     print(f"Processed {i + 1}/{len(font_list)} font files...")
        except Exception as e:
            print(f"Error processing font file {font_path}: {e}")
    print("Finished extracting font names.")
else:
    print("No font files found by findSystemFonts.")

# 使用 Pandas Series 方便查看和搜索
if font_names:
    try:
        font_series = pd.Series(sorted(list(set(font_names)))) # Define font_series here

        # 打印可能包含中文的字体（常见关键字）
        print("\n--- Potentially Chinese supporting fonts found: ---")
        chinese_keywords = ['Hei', 'Song', 'Fang', 'Kai', 'Ming', 'PingFang', 'YaHei', 'DengXian', 'Source Han', 'Noto Sans CJK', 'WenQuanYi', 'SimSun', 'STHeiti', 'STSong']
        # Use regex=True for pandas >= 1.4, handle potential warnings/errors otherwise
        try:
             possible_chinese_fonts = font_series[font_series.str.contains('|'.join(chinese_keywords), case=False, na=False, regex=True)]
        except TypeError: # Handle older pandas versions maybe?
             possible_chinese_fonts = font_series[font_series.str.contains('|'.join(chinese_keywords), case=False, na=False)]

        if not possible_chinese_fonts.empty:
            print(possible_chinese_fonts.to_string())
        else:
            print("No fonts found matching common Chinese keywords.")

        print("\n--- All fonts found: ---")
        print(font_series.to_string()) # Now print it
    except Exception as e:
        print(f"Error creating or printing pandas Series: {e}")
        print("\n--- Raw font names list (if available): ---")
        print(sorted(list(set(font_names))))
else:
    print("\nCould not extract any font names.")
