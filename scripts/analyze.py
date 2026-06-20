import os
import re
import sys
from collections import Counter
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.data.characters import (
    ISO_PATTERNS, KNOWN_CHARACTERS, NOISE_WORDS, URGENCY_WORDS,
    CHARACTER_ALIASES, SERIES_HINT, SERIES_KEYWORDS,
    load_data, find_iso_tweets, classify_urgency, analyze_character_urgency,
    extract_characters
)

sns.set_style('whitegrid')
plt.rcParams.update({'figure.max_open_warning': 0, 'font.size': 10})

CSV_PATH = 'data/comifuro_tweets.csv'
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_general_data():
    if not os.path.isfile(CSV_PATH):
        print(f"File {CSV_PATH} tidak ditemukan. Jalankan scraper dulu.")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df['month'] = pd.Categorical(df['month'], ordered=True)
    df['hour'] = pd.to_numeric(df['hour'], errors='coerce')
    df['favorite_count'] = pd.to_numeric(df['favorite_count'], errors='coerce').fillna(0)
    df['retweet_count'] = pd.to_numeric(df['retweet_count'], errors='coerce').fillna(0)
    df['engagement'] = df['favorite_count'] + df['retweet_count']
    return df


def load_char_data():
    if not os.path.isfile(CSV_PATH):
        print(f"File {CSV_PATH} tidak ditemukan")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df['full_text'] = df['full_text'].fillna('').astype(str)
    return df


def plot_top_keywords(df):
    top = df['keyword'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette('viridis', len(top))
    top.plot(kind='barh', color=colors[::-1], ax=ax)
    ax.set_title('Top 15 Keyword Paling Banyak Muncul', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jumlah Tweet')
    ax.set_ylabel('Keyword')
    ax.invert_yaxis()
    for i, v in enumerate(top.values):
        ax.text(v + 0.5, i, str(v), va='center', fontsize=9)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/top_keywords.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] top_keywords.png")
    return top


def plot_top_users(df):
    top = df['user_screen_name'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette('magma', len(top))
    top.plot(kind='barh', color=colors[::-1], ax=ax)
    ax.set_title('Top 15 User Paling Aktif Ngetweet', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jumlah Tweet')
    ax.set_ylabel('User')
    ax.invert_yaxis()
    for i, v in enumerate(top.values):
        ax.text(v + 0.5, i, str(v), va='center', fontsize=9)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/top_users.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] top_users.png")


def plot_tweets_by_month(df):
    month_order = sorted(df['month'].dropna().unique())
    counts = df['month'].value_counts().reindex(month_order).fillna(0)
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(range(len(counts)), counts.values, alpha=0.3, color='#2ecc71')
    ax.plot(range(len(counts)), counts.values, marker='o', color='#27ae60', linewidth=2)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(counts.index, rotation=45, ha='right', fontsize=8)
    ax.set_title('Tren Tweet per Bulan (2024-2026)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Jumlah Tweet')
    ax.margins(x=0.02)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/tweets_by_month.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] tweets_by_month.png")


def plot_top_tweets(df):
    top = df.nlargest(10, 'engagement')[['full_text', 'engagement', 'user_screen_name']]
    labels = [f'@{row["user_screen_name"]}' for _, row in top.iterrows()]
    texts = [row['full_text'][:50] + '...' for _, row in top.iterrows()]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top)), top['engagement'].values, color=sns.color_palette('Reds_r', len(top)))
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f'{l} — {t}' for l, t in zip(labels, texts)], fontsize=8)
    ax.set_title('Top 10 Tweet dengan Engagement Tertinggi', fontsize=14, fontweight='bold')
    ax.set_xlabel('Total Engagement (Likes + Retweets)')
    ax.invert_yaxis()
    for bar, v in zip(bars, top['engagement'].values):
        ax.text(v + 0.5, bar.get_y() + bar.get_height() / 2, str(int(v)), va='center', fontsize=9)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/top_tweets.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] top_tweets.png")


def plot_wordcloud(df):
    text = ' '.join(df['full_text'].dropna().tolist())
    wc = WordCloud(
        width=1600, height=800,
        background_color='white',
        max_words=150,
        colormap='viridis',
        collocations=False
    ).generate(text)
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Word Cloud — Isi Tweet', fontsize=16, fontweight='bold')
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/wordcloud.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] wordcloud.png")


def plot_hourly_activity(df):
    hour_counts = df['hour'].value_counts().sort_index()
    all_hours = pd.Series(0, index=range(24))
    all_hours.update(hour_counts)
    fig, ax = plt.subplots(figsize=(12, 4))
    colors = ['#e74c3c' if v == all_hours.max() else '#3498db' for v in all_hours.values]
    ax.bar(all_hours.index, all_hours.values, color=colors, edgecolor='white', linewidth=0.5)
    ax.set_xticks(range(24))
    ax.set_title('Aktivitas Tweet per Jam', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jam (UTC+7)')
    ax.set_ylabel('Jumlah Tweet')
    ax.margins(x=0.02)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/hourly_activity.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] hourly_activity.png")


def print_summary(df):
    total = len(df)
    unique_users = df['user_screen_name'].nunique()
    unique_keywords = df['keyword'].nunique()
    date_range = ''
    if not df['date'].dropna().empty:
        date_range = f"{df['date'].min()} s/d {df['date'].max()}"
    avg_engagement = df['engagement'].mean()

    print()
    print("=" * 50)
    print("  RINGKASAN DATA")
    print("=" * 50)
    print(f"  Total tweet        : {total}")
    print(f"  Unique users        : {unique_users}")
    print(f"  Unique keywords     : {unique_keywords}")
    print(f"  Rentang tanggal     : {date_range}")
    print(f"  Rata-rata engagement: {avg_engagement:.1f}")
    print(f"  Keyword terbanyak   : {df['keyword'].value_counts().index[0]} ({df['keyword'].value_counts().values[0]})")
    print(f"  User paling aktif   : {df['user_screen_name'].value_counts().index[0]} ({df['user_screen_name'].value_counts().values[0]})")
    print("=" * 50)


def plot_top_wanted(all_found_counter):
    top = all_found_counter.most_common(20)
    if not top:
        print("  (no characters found)")
        return
    names, counts = zip(*top)

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = sns.color_palette('rocket_r', len(names))
    ax.barh(range(len(names)), counts, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_title('Top 20 Karakter Paling Banyak Dicari / Diburu', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jumlah Tweet ISO')

    for bar, v in zip(ax.patches, counts):
        ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2, str(v), va='center', fontsize=9)

    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/top_wanted_characters.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] top_wanted_characters.png")


def plot_iso_ratio(df, df_iso):
    total = len(df)
    iso_count = len(df_iso)
    other = total - iso_count

    fig, ax = plt.subplots(figsize=(5, 5))
    colors = ['#e74c3c', '#3498db']
    ax.pie([iso_count, other],
           labels=[f'ISO / Cari ({iso_count})', f'Lainnya ({other})'],
           colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
    ax.set_title('Proporsi Tweet "Mencari/Mau Beli"', fontsize=13, fontweight='bold')
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/iso_vs_jual.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] iso_vs_jual.png")


def plot_iso_wordcloud(df_iso):
    text = ' '.join(df_iso['full_text'].dropna().tolist())
    if not text.strip():
        return
    wc = WordCloud(width=1600, height=800, background_color='white',
                   max_words=120, colormap='plasma', collocations=False).generate(text)
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Word Cloud — Tweet "Mencari / Mau Beli"', fontsize=16, fontweight='bold')
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/wordcloud_iso.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] wordcloud_iso.png")


def plot_monthly_trend_char(df_iso, all_found_counter):
    top_chars = [c for c, _ in all_found_counter.most_common(10)]
    if not top_chars:
        return

    df_iso['month'] = pd.to_datetime(df_iso['date'], errors='coerce').dt.to_period('M').astype(str)
    char_counts = {}
    for char in top_chars:
        mask = df_iso['full_text'].str.contains(re.escape(char), case=False, na=False)
        char_counts[char] = df_iso[mask].groupby('month').size()

    months = sorted(set().union(*[list(v.index) for v in char_counts.values() if not v.empty]))
    if not months:
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = sns.color_palette('tab10', len(top_chars))
    x = range(len(months))

    for i, (char, counts) in enumerate(char_counts.items()):
        vals = [counts.get(m, 0) for m in months]
        ax.plot(x, vals, marker='o', label=char, color=colors[i], linewidth=2, markersize=4)

    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right', fontsize=8)
    ax.set_title('Tren Pencarian Karakter per Bulan (Top 10)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Jumlah Tweet "Cari"')
    ax.legend(fontsize=7, ncol=2)
    ax.margins(x=0.02)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/trend_karakter.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] trend_karakter.png")


def plot_urgency_top_chars(char_data, top_n=15):
    chars = sorted(char_data.items(),
                   key=lambda x: (x[1]['desperate'], x[1]['score_sum']),
                   reverse=True)[:top_n]
    if not chars:
        return
    names = []
    desperate_counts = []
    total_counts = []
    for name, data in chars:
        names.append(name)
        desperate_counts.append(data['desperate'])
        total_counts.append(data['total'])

    fig, ax = plt.subplots(figsize=(11, 7))
    y = range(len(names))
    ax.barh(y, total_counts, height=0.6, color='#d4d4d4', label='Total ISO', alpha=0.5)
    ax.barh(y, desperate_counts, height=0.6, color='#e74c3c', label='Desperate')
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_title('Top 15 Karakter Paling "Desperate" (Level Keparahan Pencarian)',
                  fontsize=13, fontweight='bold')
    ax.set_xlabel('Jumlah Tweet')
    ax.legend(fontsize=10)
    for bar, d, t in zip(ax.patches[:len(chars)], desperate_counts, total_counts):
        ax.text(d + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{d}/{t}', va='center', fontsize=8)
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/urgency_top_chars.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] urgency_top_chars.png")


def plot_urgency_distribution(df_iso):
    labels = []
    for text in df_iso['full_text']:
        label, _ = classify_urgency(text)
        labels.append(label)
    counts = Counter(labels)
    if not counts:
        return

    fig, ax = plt.subplots(figsize=(5, 5))
    colors_map = {'Desperate': '#e74c3c', 'Normal': '#f39c12', 'Santai': '#3498db'}
    colors = [colors_map.get(k, '#95a5a6') for k in counts.keys()]
    ax.pie(counts.values(),
           labels=[f'{k} ({v})' for k, v in counts.items()],
           colors=colors, autopct='%1.1f%%', startangle=90,
           textprops={'fontsize': 11})
    ax.set_title('Distribusi Urgency Tweet ISO', fontsize=13, fontweight='bold')
    plt.tight_layout()
    fig.savefig(f'{OUTPUT_DIR}/urgency_distribution.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] urgency_distribution.png")


def print_char_summary(df_iso, all_found_counter, char_urgency=None):
    print()
    print("=" * 55)
    print("  RINGKASAN KARAKTER PALING DICARI")
    print("=" * 55)
    print(f"  Total tweet ISO/cari : {len(df_iso)}")
    print(f"  Total karakter unik  : {len(all_found_counter)}")
    print()
    print(f"  Top 15 Karakter Diburu:")
    for i, (char, count) in enumerate(all_found_counter.most_common(15), 1):
        print(f"    {i:2d}. {char:40s} {count:2d}x")
    print("=" * 55)

    if char_urgency:
        desperate = sorted(char_urgency.items(),
                           key=lambda x: (x[1]['desperate'], x[1]['score_sum']),
                           reverse=True)[:5]
        if desperate and desperate[0][1]['desperate'] > 0:
            print()
            print(f"  Top 5 Karakter PALING DESPERATE 🔥:")
            for i, (char, data) in enumerate(desperate, 1):
                pct = data['desperate'] / max(data['total'], 1) * 100
                print(f"    {i:2d}. {char:40s} {data['desperate']:2d}x desperate ({pct:.0f}%)")
            print("=" * 55)


def main():
    # --- General Analysis ---
    print(">> Loading data...")
    df = load_general_data()
    print(f">> {len(df)} tweet loaded\n")

    print(">> Generating general charts...")
    print("-" * 40)
    plot_top_keywords(df)
    plot_top_users(df)
    plot_tweets_by_month(df)
    plot_top_tweets(df)
    plot_wordcloud(df)
    plot_hourly_activity(df)
    print("-" * 40)

    print_summary(df)

    print(f"\n>> General charts saved to '{OUTPUT_DIR}/'\n")

    # --- Character Analysis ---
    print(">> Loading character data...")
    df_char = load_char_data()
    print(f">> {len(df_char)} tweet loaded\n")

    print(">> Mencari tweet ISO / mencari / mau beli...")
    df_iso = find_iso_tweets(df_char)
    print(f">> Ditemukan {len(df_iso)} tweet dengan intent cari/beli\n")

    print(">> Extract nama karakter...")
    all_found = []
    for text in df_iso['full_text']:
        chars = extract_characters(text)
        all_found.extend(chars)

    all_found_counter = Counter(all_found)

    print(f">> Total karakter terdeteksi: {len(all_found_counter)} unik\n")

    print(">> Generating charts karakter...")
    print("-" * 40)
    plot_top_wanted(all_found_counter)
    plot_iso_ratio(df_char, df_iso)
    plot_iso_wordcloud(df_iso)
    plot_monthly_trend_char(df_iso, all_found_counter)
    print("-" * 40)

    print(">> Analisis urgency...")
    print("-" * 40)
    char_urgency = analyze_character_urgency(df_iso, all_found_counter)
    plot_urgency_top_chars(char_urgency)
    plot_urgency_distribution(df_iso)
    print("-" * 40)

    print_char_summary(df_iso, all_found_counter, char_urgency)

    print(f"\n>> Semua chart tersimpan di folder '{OUTPUT_DIR}/'")


if __name__ == '__main__':
    main()
