import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import statsmodels.api as smb
from helper import load_data, transform_df, filter_df, select_cols, calc_ms, calc_api, calc_spi,quarter_sort_key, calc_tdp_share, calc_mix_adjusted_api,calc_mix_adjusted_spi,calc_ppi,calc_promo_proxy,calc_vpp

st.set_page_config(layout="wide")
st.title("Brand Competitiveness Dashboard")

uploaded_file = st.sidebar.file_uploader(
    label="Upload your Excel file", 
    type=["xlsx"]
)

if uploaded_file is not None:
    df = load_data(uploaded_file)

    id_cols = [
        'Facts','Markets','CATEGORY','SEGMENT',
        'MANUFACTURER','BRAND','SUBBRAND',
        'BASEPACKRANGE','BASEPACKSIZE'
    ]

    df = df[[col for col in df.columns if not col.startswith('L')]]

    df_transformed = transform_df(df)

    market = st.selectbox('Market',sorted(df_transformed['Markets'].unique()))

    category = st.selectbox('Category',sorted(df_transformed['CATEGORY'].unique()))

    segment = st.selectbox('Segment',['ALL'] + sorted(df_transformed['SEGMENT'].unique()))

    df_transformed = df_transformed[(df_transformed['Markets'] == market) & (df_transformed['CATEGORY'] == category)]

    if segment == 'ALL':
        sorted_range = df_transformed['BASEPACKRANGE'].dropna().unique().tolist()
    else:
        sorted_range = df_transformed[df_transformed['SEGMENT'] == segment]['BASEPACKRANGE'].dropna().unique().tolist()

    basepackrange = st.selectbox(
        'Basepackrange',
        ['ALL'] + sorted(sorted_range)
    )

    col1,col2 = st.columns(2)

    with col1:
        if segment != 'ALL':
            mfg_options1 = sorted(
                df_transformed[
                    df_transformed['SEGMENT'] == segment
                ]['MANUFACTURER'].unique()
            )
        else:
            mfg_options1 = sorted(
                df_transformed['MANUFACTURER'].unique()
            )

        default_index = mfg_options1.index('HINDUSTAN UNILEVER LIMITED') if 'HINDUSTAN UNILEVER LIMITED' in mfg_options1 else 0

        selected_mfg1 = st.selectbox(
            'Manufacturer',
            mfg_options1,
            index=default_index
        )

    with col2:
        if segment != 'ALL':
            mfg_options2 = sorted(
                df_transformed[
                    df_transformed['SEGMENT'] == segment
                ]['MANUFACTURER'].unique()
            )
        else:
            mfg_options2 = sorted(
                df_transformed['MANUFACTURER'].unique()
            )

        mfg_options2 = [mfg for mfg in mfg_options2 if mfg != selected_mfg1]
        
        if not mfg_options2:
            st.warning("No competitor available.")
            st.stop()


        selected_mfg2 = st.selectbox(
            'Manufacturer',
            mfg_options2
        )

    col3,col4 = st.columns(2)

    with col3:
        if segment != 'ALL':
            brand_option1 = st.selectbox('Brand',
            sorted(
                df_transformed[
                    (df_transformed['SEGMENT'] == segment) & 
                    (df_transformed['MANUFACTURER'] == selected_mfg1)
                ]['BRAND'].dropna().unique().tolist()
            )
            )
        else:
            brand_option1 = st.selectbox('Brand',
            sorted(
                df_transformed[
                    (df_transformed['MANUFACTURER'] == selected_mfg1)
                ]['BRAND'].dropna().unique().tolist()
            )
            )
    with col4:
        if segment != 'ALL':
            brand_option2 = st.selectbox('Brand',
            sorted(
                df_transformed[
                    (df_transformed['SEGMENT'] == segment) & 
                    (df_transformed['MANUFACTURER'] == selected_mfg2)
                ]['BRAND'].dropna().unique().tolist()
            )
            )
        else:
            brand_option2 = st.selectbox('Brand',
            sorted(
                df_transformed[
                    (df_transformed['MANUFACTURER'] == selected_mfg2)
                ]['BRAND'].dropna().unique().tolist()
            )
            )

    col5,col6 = st.columns(2)

    with col5:
        if segment != 'ALL':
            if brand_option1 != 'ALL':
                subbrand_option1 = st.selectbox('Subbrand',
                ['ALL'] + sorted(
                    df_transformed[
                        (df_transformed['SEGMENT'] == segment) & 
                        (df_transformed['MANUFACTURER'] == selected_mfg1) &
                        (df_transformed['BRAND'] == brand_option1)
                    ]['SUBBRAND'].dropna().unique().tolist()
                )
                )
        else:
            if brand_option1 != 'ALL':
                subbrand_option1 = st.selectbox('Subbrand',
                ['ALL'] + sorted(
                    df_transformed[
                        (df_transformed['MANUFACTURER'] == selected_mfg1) &
                        (df_transformed['BRAND'] == brand_option1)
                    ]['SUBBRAND'].dropna().unique().tolist()
                )
                )

    with col6:
        if segment != 'ALL':
            if brand_option2 != 'ALL':
                subbrand_option2 = st.selectbox('Subbrand',
                ['ALL'] + sorted(
                    df_transformed[
                        (df_transformed['SEGMENT'] == segment) & 
                        (df_transformed['MANUFACTURER'] == selected_mfg2) &
                        (df_transformed['BRAND'] == brand_option2)
                    ]['SUBBRAND'].dropna().unique().tolist()
                )
                )
        else:
            if brand_option2 != 'ALL':
                subbrand_option2 = st.selectbox('Subbrand',
                ['ALL'] + sorted(
                    df_transformed[ 
                        (df_transformed['MANUFACTURER'] == selected_mfg2) &
                        (df_transformed['BRAND'] == brand_option2)
                    ]['SUBBRAND'].dropna().unique().tolist()
                )
                )

    df_filtered = filter_df(df_transformed,category=category,segment=segment,basepackrange=basepackrange)

    selected_col_df = select_cols(df_filtered,subbrand=subbrand_option1,basepackrange=basepackrange)

    ms_df = calc_ms(selected_col_df,mfg=selected_mfg1,brand=brand_option1,subbrand=subbrand_option1)

    spi_df = calc_spi(selected_col_df,mfg1=selected_mfg1,brand1=brand_option1,mfg2=selected_mfg2,
    brand2=brand_option2,subbrand1=subbrand_option1,subbrand2=subbrand_option2)

    final_df = ms_df.merge(spi_df,on='Quarter',how='left')

    final_df = final_df.sort_values(
        by='Quarter',
        key=lambda x: x.map(quarter_sort_key)
    )

    entity1 = (
        subbrand_option1
        if subbrand_option1 != 'ALL'
        else brand_option1
    )

    entity2 = (
        subbrand_option2
        if subbrand_option2 != 'ALL'
        else brand_option2
    )

    chart_title = f"SPI vs Market Share Trend: {entity1} vs {entity2}"

    if basepackrange != 'ALL':
        chart_title += f" | {basepackrange}"

    tab1, tab2, tab3, tab4 = st.tabs([
        "SPI vs MS Val",
        "TDP Share & Productivity Index (PPI)",
        "Mix-Adjusted SPI",
        "Promo-Intensity Proxy"
    ])

    with tab1:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=final_df["Quarter"],
                y=final_df["MS"],
                mode="lines+markers",
                name="MS Val %",
                line=dict(color="#1F77B4", width=3),  
                marker=dict(size=8)

            )
        )

        fig.add_trace(
            go.Scatter(
                x=final_df["Quarter"],
                y=final_df["SPI"],
                mode="lines+markers",
                name="SPI",
                yaxis="y2",
                line=dict(color="#FF7F0E", width=3),  # Orange
                marker=dict(size=8)

            )
        )

        fig.update_layout(
            yaxis=dict(title="Market Share %",range=[0, final_df["MS"].max() * 1.1]),
            yaxis2=dict(
                title="SPI",
                overlaying="y",
                side="right",
                range=[0, final_df["SPI"].max() * 1.1]
            ),
            title={
                    "text": chart_title,
                    "x": 0.5,          
                    "xanchor": "center"
                }

        )
        fig.update_yaxes(showgrid=False)

        st.plotly_chart(fig, width="stretch")

        scatter_fig = px.scatter(
            final_df,
            x="SPI",
            y="MS",
            text="Quarter",
            trendline="ols",
            title=f"SPI vs Market Share Relationship: {entity1} vs {entity2}"
        )

        scatter_fig.update_traces(
            textposition="top center"
        )

        st.plotly_chart(scatter_fig, width="stretch")

        st.metric("SPI vs MS correlation (r)", round(final_df["SPI"].corr(final_df["MS"]), 3))

    # ---------------------------------------------------------------------------
    # TAB 2: TDP Share (distribution reach) & PPI (distribution productivity)
    # TDP is additive across basepack ranges/SKUs, so this rolls up cleanly even
    # where %WD can't be summed.
    # ---------------------------------------------------------------------------

    with tab2:
        st.caption(
            "TDP Share is a distribution-reach share (safely additive, unlike %WD). "
            "PPI = relative Sales Val per TDP point — a distribution-productivity index, "
            "the structural analogue of SPI on the reach/pull axis instead of price."
        )

        tdp_df = calc_tdp_share(
            selected_col_df,
            mfg1=selected_mfg1, brand1=brand_option1,
            mfg2=selected_mfg2, brand2=brand_option2,
            subbrand1=subbrand_option1, subbrand2=subbrand_option2
        )
        ppi_df = calc_ppi(
            selected_col_df,
            mfg1=selected_mfg1, brand1=brand_option1,
            mfg2=selected_mfg2, brand2=brand_option2,
            subbrand1=subbrand_option1, subbrand2=subbrand_option2
        )

        tdp_final_df = ms_df.merge(tdp_df, on='Quarter', how='left').merge(ppi_df, on='Quarter', how='left')
        tdp_final_df = tdp_final_df.sort_values(by='Quarter', key=lambda x: x.map(quarter_sort_key))

        fig_tdp = go.Figure()

        fig_tdp.add_trace(
            go.Scatter(
                x=tdp_final_df["Quarter"], y=tdp_final_df["MS"],
                mode="lines+markers", name="MS Val %",
                line=dict(color="#1F77B4", width=3), marker=dict(size=8)
            )
        )
        fig_tdp.add_trace(
            go.Scatter(
                x=tdp_final_df["Quarter"], y=tdp_final_df["TDP Share"],
                mode="lines+markers", name="TDP Share %", yaxis="y2",
                line=dict(color="#2CA02C", width=3), marker=dict(size=8)
            )
        )
        fig_tdp.add_trace(
            go.Scatter(
                x=tdp_final_df["Quarter"], y=tdp_final_df["PPI"],
                mode="lines+markers", name="PPI", yaxis="y2",
                line=dict(color="#9467BD", width=3, dash="dot"), marker=dict(size=8)
            )
        )

        fig_tdp.update_layout(
            yaxis=dict(title="Market Share %"),
            yaxis2=dict(title="TDP Share % / PPI", overlaying="y", side="right"),
            title={"text": f"MS Val vs TDP Share vs PPI: {entity1} vs {entity2}", "x": 0.5, "xanchor": "center"}
        )
        fig_tdp.update_yaxes(showgrid=False)

        st.plotly_chart(fig_tdp, width="stretch")

        col_a, col_b = st.columns(2)
        with col_a:
            scatter_ppi = px.scatter(
                tdp_final_df, x="PPI", y="MS", text="Quarter", trendline="ols",
                title="PPI vs MS Val"
            )
            scatter_ppi.update_traces(textposition="top center")
            st.plotly_chart(scatter_ppi, width="stretch")
            st.metric("PPI vs MS correlation (r)", round(tdp_final_df["PPI"].corr(tdp_final_df["MS"]), 3))

        with col_b:
            scatter_tdp = px.scatter(
                tdp_final_df, x="TDP Share", y="MS", text="Quarter", trendline="ols",
                title="TDP Share vs MS Val"
            )
            scatter_tdp.update_traces(textposition="top center")
            st.plotly_chart(scatter_tdp, width="stretch")
            st.metric("TDP Share vs MS correlation (r)", round(tdp_final_df["TDP Share"].corr(tdp_final_df["MS"]), 3))

    # ---------------------------------------------------------------------------
    # TAB 3: Mix-adjusted SPI — isolates real relative-price movement from
    # basepack-range mix shifts. Uses df_filtered (pre select_cols) since it still
    # carries BASEPACKRANGE.
    # ---------------------------------------------------------------------------

    with tab3:
        st.caption(
            "Mix-adjusted SPI freezes each brand's basepack-range value weights at a "
            "base quarter, then re-prices using that quarter's mix. The gap between "
            "actual (blended) SPI and mix-adjusted SPI is the portion of the SPI trend "
            "driven by pack-mix shifts rather than genuine relative pricing."
        )

        available_quarters = sorted(df_filtered['Quarter'].unique(), key=quarter_sort_key)
        base_quarter_choice = st.selectbox(
            'Base quarter for mix weights',
            available_quarters,
            index=0
        )

        mix_spi_df, base_quarter_used = calc_mix_adjusted_spi(
            df_filtered,
            mfg1=selected_mfg1, brand1=brand_option1,
            mfg2=selected_mfg2, brand2=brand_option2,
            subbrand1=subbrand_option1, subbrand2=subbrand_option2,
            base_quarter=base_quarter_choice
        )

        mix_final_df = final_df.merge(mix_spi_df, on='Quarter', how='left')
        mix_final_df = mix_final_df.sort_values(by='Quarter', key=lambda x: x.map(quarter_sort_key))
        mix_final_df['Mix_Effect'] = mix_final_df['SPI'] - mix_final_df['Mix_Adj_SPI']

        fig_mix = go.Figure()
        fig_mix.add_trace(
            go.Scatter(
                x=mix_final_df["Quarter"], y=mix_final_df["SPI"],
                mode="lines+markers", name="Actual (blended) SPI",
                line=dict(color="#FF7F0E", width=3), marker=dict(size=8)
            )
        )
        fig_mix.add_trace(
            go.Scatter(
                x=mix_final_df["Quarter"], y=mix_final_df["Mix_Adj_SPI"],
                mode="lines+markers", name="Mix-Adjusted SPI",
                line=dict(color="#17BECF", width=3, dash="dash"), marker=dict(size=8)
            )
        )
        fig_mix.update_layout(
            yaxis=dict(title="SPI"),
            title={
                "text": f"Actual vs Mix-Adjusted SPI (base: {base_quarter_used}): {entity1} vs {entity2}",
                "x": 0.5, "xanchor": "center"
            }
        )
        st.plotly_chart(fig_mix, width="stretch")

        fig_mix_effect = px.bar(
            mix_final_df, x="Quarter", y="Mix_Effect",
            title="Mix Effect on SPI (Actual SPI − Mix-Adjusted SPI)"
        )
        st.plotly_chart(fig_mix_effect, width="stretch")

        st.dataframe(
            mix_final_df[['Quarter', 'MS', 'SPI', 'Mix_Adj_SPI', 'Mix_Effect']],
            width="stretch"
        )

    # ---------------------------------------------------------------------------
    # TAB 4: Promo-intensity proxy from API volatility (no promo/scheme data
    # available, so this is inferred from quarter-over-quarter API swings).
    # ---------------------------------------------------------------------------

    with tab4:
        st.caption(
            "No promo/scheme flag exists in this data, so this proxies promotional "
            "activity from API volatility: sharp API dips are a common signature of "
            "scheme-driven price cuts rather than genuine base-price moves. Cross-check "
            "against the TDP Share tab — a volatility spike with flat TDP is more "
            "likely promo than a real distribution-driven price change."
        )

        window = st.slider('Rolling window (quarters)', min_value=2, max_value=8, value=4)

        api_a = calc_api(selected_col_df, mfg=selected_mfg1, brand=brand_option1, subbrand=subbrand_option1)
        api_b = calc_api(selected_col_df, mfg=selected_mfg2, brand=brand_option2, subbrand=subbrand_option2)

        promo_a = calc_promo_proxy(api_a, window=window).rename(
            columns={'API': f'API_{entity1}', 'API_QoQ_Change': f'QoQ_{entity1}', 'API_Volatility': f'Vol_{entity1}'}
        )
        promo_b = calc_promo_proxy(api_b, window=window).rename(
            columns={'API': f'API_{entity2}', 'API_QoQ_Change': f'QoQ_{entity2}', 'API_Volatility': f'Vol_{entity2}'}
        )

        promo_final_df = promo_a.merge(promo_b, on='Quarter', how='left').merge(
            ms_df, on='Quarter', how='left'
        )
        promo_final_df = promo_final_df.sort_values(by='Quarter', key=lambda x: x.map(quarter_sort_key))

        fig_promo = go.Figure()
        fig_promo.add_trace(
            go.Scatter(
                x=promo_final_df["Quarter"], y=promo_final_df[f'Vol_{entity1}'],
                mode="lines+markers", name=f"API Volatility: {entity1}",
                line=dict(color="#D62728", width=3), marker=dict(size=8)
            )
        )
        fig_promo.add_trace(
            go.Scatter(
                x=promo_final_df["Quarter"], y=promo_final_df[f'Vol_{entity2}'],
                mode="lines+markers", name=f"API Volatility: {entity2}",
                line=dict(color="#8C564B", width=3), marker=dict(size=8)
            )
        )
        fig_promo.add_trace(
            go.Scatter(
                x=promo_final_df["Quarter"], y=promo_final_df["MS"],
                mode="lines+markers", name="MS Val %", yaxis="y2",
                line=dict(color="#1F77B4", width=2, dash="dot"), marker=dict(size=6)
            )
        )
        fig_promo.update_layout(
            yaxis=dict(title="API Volatility (rolling std)"),
            yaxis2=dict(title="Market Share %", overlaying="y", side="right"),
            title={"text": f"Promo-Intensity Proxy vs MS Val: {entity1} vs {entity2}", "x": 0.5, "xanchor": "center"}
        )
        st.plotly_chart(fig_promo, width="stretch")

        st.dataframe(promo_final_df, width="stretch")

else:
    st.info("Please upload a Excel file in the sidebar to begin.")