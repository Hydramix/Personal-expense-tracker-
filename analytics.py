import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from models import Expense, db
from datetime import datetime, date
import os, calendar

CHART_DIR = os.path.join(os.path.dirname(__file__), 'static', 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

CAT_COLORS = {
    'Food':          '#c94f2c',
    'Transport':     '#1f5fa6',
    'Bills':         '#b86e10',
    'Shopping':      '#6543b5',
    'Health':        '#2d7d4e',
    'Entertainment': '#a0364a',
    'Travel':        '#3a7f9f',
    'Education':     '#5f7a30',
    'Other':         '#7a6550',
}

def load_dataframe():
    rows = Expense.query.all()
    if not rows:
        return pd.DataFrame(columns=['id','description','amount','category','date'])
    data = [{
        'id':          e.id,
        'description': e.description,
        'amount':      e.amount,
        'category':    e.category,
        'date':        pd.to_datetime(e.date)
    } for e in rows]
    return pd.DataFrame(data)

def get_analytics(month_filter):
    df = load_dataframe()
    year, mon = int(month_filter.split('-')[0]), int(month_filter.split('-')[1])
    month_name = datetime(year, mon, 1).strftime('%B %Y')

    # Filter current month
    if not df.empty:
        df_month = df[(df['date'].dt.year == year) & (df['date'].dt.month == mon)].copy()
    else:
        df_month = pd.DataFrame(columns=df.columns)

    # ── Summary stats ──────────────────────────────────────────────
    total_spent  = float(df_month['amount'].sum()) if not df_month.empty else 0.0
    mean_daily   = 0.0
    median_spend = 0.0
    max_spend    = 0.0
    max_day      = '—'
    top_category = '—'
    top_cat_amt  = 0.0
    num_txn      = len(df_month)

    if not df_month.empty:
        median_spend = float(np.median(df_month['amount'].values))
        max_spend    = float(df_month['amount'].max())
        max_row      = df_month.loc[df_month['amount'].idxmax()]
        max_day      = max_row['date'].strftime('%d %b')

        daily = df_month.groupby(df_month['date'].dt.day)['amount'].sum()
        mean_daily = float(np.mean(daily.values))

        cat_totals   = df_month.groupby('category')['amount'].sum()
        top_category = cat_totals.idxmax()
        top_cat_amt  = float(cat_totals.max())

    # ── Chart 1: Category Pie Chart ────────────────────────────────
    pie_path = os.path.join(CHART_DIR, f'pie_{month_filter}.png')
    if not df_month.empty:
        cat_totals = df_month.groupby('category')['amount'].sum()
        colors     = [CAT_COLORS.get(c, '#888') for c in cat_totals.index]
        fig, ax    = plt.subplots(figsize=(6, 4), facecolor='#fffefb')
        wedges, texts, autotexts = ax.pie(
            cat_totals.values, labels=cat_totals.index,
            colors=colors, autopct='%1.1f%%', startangle=140,
            pctdistance=0.82, wedgeprops=dict(width=0.55, edgecolor='white', linewidth=2)
        )
        for t in texts:     t.set_fontsize(9);  t.set_color('#3a2a15')
        for t in autotexts: t.set_fontsize(8);  t.set_color('white'); t.set_fontweight('bold')
        ax.set_title(f'Category Breakdown – {month_name}', fontsize=12, color='#1a1208', pad=12)
        plt.tight_layout()
        plt.savefig(pie_path, dpi=120, bbox_inches='tight', facecolor='#fffefb')
        plt.close()
    else:
        _empty_chart(pie_path, 'No data for this month')

    # ── Chart 2: Monthly Trend Bar Chart (6 months) ────────────────
    trend_path = os.path.join(CHART_DIR, f'trend_{month_filter}.png')
    months_data, month_labels = [], []
    for i in range(5, -1, -1):
        m2 = mon - i
        y2 = year
        while m2 <= 0: m2 += 12; y2 -= 1
        lbl = datetime(y2, m2, 1).strftime('%b %y')
        month_labels.append(lbl)
        if not df.empty:
            val = df[(df['date'].dt.year == y2) & (df['date'].dt.month == m2)]['amount'].sum()
        else:
            val = 0
        months_data.append(float(val))

    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor='#fffefb')
    bar_colors = ['#d4c5b0'] * 5 + ['#c94f2c']
    bars = ax.bar(month_labels, months_data, color=bar_colors, edgecolor='white',
                  linewidth=1.5, width=0.55)
    for bar, val in zip(bars, months_data):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(months_data)*0.02,
                    f'₹{int(val):,}', ha='center', va='bottom', fontsize=8, color='#6b5c45')
    ax.set_facecolor('#fffefb')
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#d4c5b0')
    ax.tick_params(colors='#6b5c45', labelsize=9)
    ax.set_ylabel('Amount (₹)', color='#6b5c45', fontsize=9)
    ax.set_title('Monthly Spending Trend', fontsize=12, color='#1a1208', pad=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'₹{int(x):,}'))
    fig.patch.set_facecolor('#fffefb')
    plt.tight_layout()
    plt.savefig(trend_path, dpi=120, bbox_inches='tight', facecolor='#fffefb')
    plt.close()

    # ── Chart 3: Day-wise Line Chart ───────────────────────────────
    line_path = os.path.join(CHART_DIR, f'line_{month_filter}.png')
    if not df_month.empty:
        daily_spend = df_month.groupby(df_month['date'].dt.day)['amount'].sum()
        days_in_month = calendar.monthrange(year, mon)[1]
        all_days = pd.Series(0.0, index=range(1, days_in_month + 1))
        all_days.update(daily_spend)

        fig, ax = plt.subplots(figsize=(7, 3.2), facecolor='#fffefb')
        ax.fill_between(all_days.index, all_days.values, alpha=0.15, color='#c94f2c')
        ax.plot(all_days.index, all_days.values, color='#c94f2c', linewidth=2, marker='o',
                markersize=4, markerfacecolor='white', markeredgewidth=1.5)
        ax.axhline(mean_daily, color='#b86e10', linestyle='--', linewidth=1.2, alpha=0.7,
                   label=f'Avg ₹{mean_daily:,.0f}/day')
        ax.set_facecolor('#fffefb')
        ax.spines[['top','right']].set_visible(False)
        ax.spines[['left','bottom']].set_color('#d4c5b0')
        ax.tick_params(colors='#6b5c45', labelsize=9)
        ax.set_xlabel('Day of Month', color='#6b5c45', fontsize=9)
        ax.set_ylabel('Amount (₹)', color='#6b5c45', fontsize=9)
        ax.set_title(f'Daily Spending – {month_name}', fontsize=12, color='#1a1208', pad=10)
        ax.legend(fontsize=9, framealpha=0.5)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'₹{int(x):,}'))
        fig.patch.set_facecolor('#fffefb')
        plt.tight_layout()
        plt.savefig(line_path, dpi=120, bbox_inches='tight', facecolor='#fffefb')
        plt.close()
    else:
        _empty_chart(line_path, 'No data for this month')

    # ── Chart 4: Budget vs Actual ──────────────────────────────────
    budget_chart_path = os.path.join(CHART_DIR, f'budget_{month_filter}.png')
    # will be rendered in template with budget value

    return dict(
        total_spent=total_spent,
        mean_daily=mean_daily,
        median_spend=median_spend,
        max_spend=max_spend,
        max_day=max_day,
        top_category=top_category,
        top_cat_amt=top_cat_amt,
        num_txn=num_txn,
        month_name=month_name,
        pie_chart=f'charts/pie_{month_filter}.png',
        trend_chart=f'charts/trend_{month_filter}.png',
        line_chart=f'charts/line_{month_filter}.png',
        cat_data={c: float(df_month[df_month['category']==c]['amount'].sum())
                  for c in df_month['category'].unique()} if not df_month.empty else {},
    )

def _empty_chart(path, msg):
    fig, ax = plt.subplots(figsize=(6, 3.5), facecolor='#fffefb')
    ax.text(0.5, 0.5, msg, ha='center', va='center', fontsize=13,
            color='#a08060', transform=ax.transAxes)
    ax.axis('off')
    fig.patch.set_facecolor('#fffefb')
    plt.savefig(path, dpi=100, bbox_inches='tight', facecolor='#fffefb')
    plt.close()
