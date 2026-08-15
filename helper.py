import pandas as pd
import streamlit as st


id_cols = [
    'Facts','Markets','CATEGORY','SEGMENT',
    'MANUFACTURER','BRAND','SUBBRAND',
    'BASEPACKRANGE','BASEPACKSIZE'
]


TDP_COL = 'TDP - Points'

@st.cache_data(show_spinner=False)
def load_data(file_path):
    return pd.read_excel(file_path)

@st.cache_data(show_spinner=False)
def transform_df(df):

    quarter_cols = [lst for lst in df.columns if lst not in id_cols]

    df_long = df.melt(id_vars=id_cols,value_vars=quarter_cols,var_name='Quarter',value_name='Value')

    df_final = (df_long.pivot_table(
        index=[
            'Markets','CATEGORY','SEGMENT',
            'MANUFACTURER','BRAND',
            'SUBBRAND','BASEPACKRANGE',
            'BASEPACKSIZE','Quarter'
        ],
        columns='Facts',
        values='Value',
        aggfunc='sum'
    )
    .reset_index()
)
    return df_final


def filter_df(df,category,segment,basepackrange):
    if segment != 'ALL':
        if basepackrange == 'ALL':
            df_filtered = df[(df['CATEGORY'] == category) & (df['SEGMENT'] == segment)]
        else:
            df_filtered = df[(df['CATEGORY'] == category) & (df['SEGMENT'] == segment) & (df['BASEPACKRANGE'] == basepackrange)]
    else:
        if basepackrange == 'ALL':
            df_filtered = df[(df['CATEGORY'] == category)]
        else:
            df_filtered = df[(df['CATEGORY'] == category) & (df['BASEPACKRANGE'] == basepackrange)]

    return df_filtered


def select_cols(df,subbrand,basepackrange):
                
    if basepackrange == 'ALL':
        if subbrand == 'ALL':
            df_dropped = df.drop(columns=['SUBBRAND','BASEPACKRANGE','BASEPACKSIZE'])
        else:
            df_dropped = df.drop(columns=['BASEPACKRANGE','BASEPACKSIZE'])
    else:
        df_filter = df[df['BASEPACKRANGE'] == basepackrange]
        if subbrand == 'ALL':
            df_dropped = df_filter.drop(columns=['SUBBRAND','BASEPACKRANGE','BASEPACKSIZE'])
        else:
            df_dropped = df_filter.drop(columns=['BASEPACKRANGE','BASEPACKSIZE'])

    return df_dropped


def calc_ms(df, mfg, brand, subbrand='ALL'):
    
    if subbrand == 'ALL':
        brand_sales = (
            df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand)]
            .groupby('Quarter', as_index=False)['Sales Val']
            .sum()
            .rename(columns={'Sales Val': 'Brand Sales'})
        )
    else:
        brand_sales = (
            df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand) & (df['SUBBRAND'] == subbrand)]
            .groupby('Quarter', as_index=False)['Sales Val']
            .sum()
            .rename(columns={'Sales Val': 'Brand Sales'})
        )

    total_sales = (
        df.groupby('Quarter', as_index=False)['Sales Val']
        .sum()
        .rename(columns={'Sales Val': 'Total Sales'})
    )

    ms_df = brand_sales.merge(total_sales, on='Quarter', how='left')
    ms_df['MS'] = (ms_df['Brand Sales'] / ms_df['Total Sales']) * 100

    return ms_df[['Quarter','MS']]


def calc_api(df,mfg,brand,subbrand='ALL'):
    if subbrand == 'ALL':
        brand_table = df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand)].groupby('Quarter', as_index=False)[['Sales Val','Sales Vol']].sum()
        brand_table['PPG'] = brand_table['Sales Val']/brand_table['Sales Vol']
    else:
        brand_table = df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand) & (df['SUBBRAND'] == subbrand)].groupby('Quarter', as_index=False)[['Sales Val','Sales Vol']].sum()
        brand_table['PPG'] = brand_table['Sales Val']/brand_table['Sales Vol']

    brand_table = brand_table[['Quarter','PPG']]

    total_table = df.groupby('Quarter', as_index=False)[['Sales Val','Sales Vol']].sum()
    total_table['Total PPG'] = total_table['Sales Val']/total_table['Sales Vol']
    total_table = total_table[['Quarter','Total PPG']]

    api_df = brand_table.merge(total_table, on='Quarter', how='left')
    api_df['API'] = (api_df['PPG'] / api_df['Total PPG']) * 100

    return api_df[['Quarter','API']]


def calc_spi(df,mfg1,brand1,mfg2,brand2,subbrand1='ALL',subbrand2='ALL'):
    manufacturer = calc_api(df,mfg1,brand1,subbrand1)
    competition = calc_api(df,mfg2,brand2,subbrand2)

    spi_df = manufacturer.merge(competition,on='Quarter',how ='left')
    spi_df['SPI'] = (spi_df['API_x']/spi_df['API_y'])*100
    return spi_df[['Quarter','SPI']]

def calc_tdp_share(df, mfg1, brand1, mfg2, brand2, subbrand1='ALL', subbrand2='ALL'):
    def brand_tdp(mfg, brand, subbrand):
        subset = df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand)]
        if subbrand != 'ALL' and 'SUBBRAND' in df.columns:
            subset = subset[subset['SUBBRAND'] == subbrand]
        return (
            subset.groupby('Quarter', as_index=False)[TDP_COL]
            .sum()
            .rename(columns={TDP_COL: 'TDP'})
        )
 
    tdp1 = brand_tdp(mfg1, brand1, subbrand1)
    tdp2 = brand_tdp(mfg2, brand2, subbrand2)
 
    merged = tdp1.merge(tdp2, on='Quarter', how='left', suffixes=('_A', '_B')).fillna(0)
    merged['TDP Share'] = (merged['TDP_A'] / (merged['TDP_A'] + merged['TDP_B'])) * 100
 
    return merged[['Quarter', 'TDP Share']]


def calc_vpp(df, mfg, brand, subbrand='ALL'):
    """
    Value Productivity per Point (VPP) = Sales Val / TDP.
    A distribution-efficiency proxy: how much value each point of distribution
    reach is pulling, independent of how wide the brand is distributed.
    """
    subset = df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand)]
    if subbrand != 'ALL' and 'SUBBRAND' in df.columns:
        subset = subset[subset['SUBBRAND'] == subbrand]
 
    t = subset.groupby('Quarter', as_index=False)[['Sales Val', TDP_COL]].sum()
    t['VPP'] = t['Sales Val'] / t[TDP_COL]
 
    return t[['Quarter', 'VPP']]


def calc_ppi(df, mfg1, brand1, mfg2, brand2, subbrand1='ALL', subbrand2='ALL'):
    """
    Productivity Index (PPI) = VPP_A / VPP_B * 100.
    The distribution-productivity analogue of SPI: instead of relative price,
    it measures relative "pull per point of distribution".
    """
    vpp1 = calc_vpp(df, mfg1, brand1, subbrand1).rename(columns={'VPP': 'VPP_A'})
    vpp2 = calc_vpp(df, mfg2, brand2, subbrand2).rename(columns={'VPP': 'VPP_B'})
 
    merged = vpp1.merge(vpp2, on='Quarter', how='left')
    merged['PPI'] = (merged['VPP_A'] / merged['VPP_B']) * 100
 
    return merged[['Quarter', 'PPI']]


def calc_mix_adjusted_api(df, mfg, brand, subbrand='ALL', base_quarter=None):
    """
    df must still contain BASEPACKRANGE (pass the pre-select_cols, basepackrange='ALL'
    filtered frame) so basepack-level API can be computed.
 
    Laspeyres-style mix-adjusted API: freezes the brand's basepack-range value
    weights at base_quarter, then re-applies those fixed weights to each quarter's
    basepack-level API. This isolates the "real" relative-price movement from a
    "mix shift" movement (e.g. brand selling more sachets vs bottles over time),
    which is a common cause of noisy brand-level SPI trends.
    """
    subset = df[(df['MANUFACTURER'] == mfg) & (df['BRAND'] == brand)]
    if subbrand != 'ALL' and 'SUBBRAND' in df.columns:
        subset = subset[subset['SUBBRAND'] == subbrand]
 
    bp_brand = subset.groupby(['Quarter', 'BASEPACKRANGE'], as_index=False)[['Sales Val', 'Sales Vol']].sum()
    bp_brand['PPG'] = bp_brand['Sales Val'] / bp_brand['Sales Vol']
 
    bp_total = df.groupby(['Quarter', 'BASEPACKRANGE'], as_index=False)[['Sales Val', 'Sales Vol']].sum()
    bp_total['Total PPG'] = bp_total['Sales Val'] / bp_total['Sales Vol']
 
    bp_merged = bp_brand.merge(
        bp_total[['Quarter', 'BASEPACKRANGE', 'Total PPG']],
        on=['Quarter', 'BASEPACKRANGE'],
        how='left'
    )
    bp_merged['API_bp'] = (bp_merged['PPG'] / bp_merged['Total PPG']) * 100
 
    if base_quarter is None:
        base_quarter = sorted(bp_merged['Quarter'].unique(), key=quarter_sort_key)[0]
 
    base_weights = bp_merged[bp_merged['Quarter'] == base_quarter][['BASEPACKRANGE', 'Sales Val']].copy()
    base_weights['Weight'] = base_weights['Sales Val'] / base_weights['Sales Val'].sum()
    base_weights = base_weights[['BASEPACKRANGE', 'Weight']]
 
    weighted = bp_merged.merge(base_weights, on='BASEPACKRANGE', how='left')
    weighted['Weight'] = weighted['Weight'].fillna(0)
    weighted['Weighted_API'] = weighted['API_bp'] * weighted['Weight']
 
    mix_adj = (
        weighted.groupby('Quarter', as_index=False)['Weighted_API']
        .sum()
        .rename(columns={'Weighted_API': 'Mix_Adj_API'})
    )
 
    return mix_adj, base_quarter

def calc_mix_adjusted_spi(df, mfg1, brand1, mfg2, brand2, subbrand1='ALL', subbrand2='ALL', base_quarter=None):
    """
    Mix-adjusted SPI = Mix_Adj_API_A / Mix_Adj_API_B * 100.
    Compare against the actual blended SPI to see how much of the SPI trend is a
    real relative-price effect vs. a pack-mix effect.
    """
    a, base_quarter = calc_mix_adjusted_api(df, mfg1, brand1, subbrand1, base_quarter)
    b, _ = calc_mix_adjusted_api(df, mfg2, brand2, subbrand2, base_quarter)
 
    merged = a.merge(b, on='Quarter', how='left', suffixes=('_A', '_B'))
    merged['Mix_Adj_SPI'] = (merged['Mix_Adj_API_A'] / merged['Mix_Adj_API_B']) * 100
 
    return merged[['Quarter', 'Mix_Adj_SPI']], base_quarter

 
def calc_promo_proxy(api_df, window=4):
    """
    api_df: DataFrame with 'Quarter' and 'API', chronologically unsorted is fine.
    Returns quarter-over-quarter API change and rolling API volatility (std dev)
    as a rough promo-intensity proxy. A sharp API dip with volume up but TDP flat
    is a classic promotional signature (not a distribution gain, so likely a
    scheme/discount rather than a genuine base-price move).
    """
    out = api_df.sort_values(by='Quarter', key=lambda x: x.map(quarter_sort_key)).copy()
    out['API_QoQ_Change'] = out['API'].diff()
    out['API_Volatility'] = out['API'].rolling(window=window, min_periods=2).std()
    return out

def quarter_sort_key(q):
    quarter, year = q.split()
    q_num = int(quarter.replace('Q', ''))
    year = int(year)
    return year * 10 + q_num