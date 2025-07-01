import streamlit as st
import pandas as pd
import plotly.express as px

# Load the CSV data
# Load and clean data
df = pd.read_csv('/Users/A200154990/ELECT_ANALYSIS/Elect/final_df.csv')
df.columns = df.columns.str.strip()

# Clean round
df['Round'] = pd.to_numeric(df['Round'], errors='coerce')
df = df.dropna(subset=['Round'])

# Aggregate if duplicates exist for Candidate+Round
df = df.groupby(['Round', 'Candidate', 'Party'], as_index=False).agg({
    'Total': 'sum',
    'Current Round': 'sum'
})

# Clean column names
df.columns = df.columns.str.strip()

# Sidebar Filters
st.sidebar.title("Election Filters")

round_options = sorted(df['Round'].dropna().unique())
candidate_options = sorted([c for c in df['Candidate'].dropna().unique() if isinstance(c, str)])

selected_round = st.sidebar.selectbox("Select Round", round_options)
selected_candidates = st.sidebar.multiselect(
    "Select Candidates to Compare", 
    options=candidate_options, 
    default=["MOHAMMED AZHARUDDIN"]
)

# Main Title
st.title("🗳️ Election Results Dashboard")

# ================================
# 🔸 Round-level Analysis
# ================================
st.subheader(f"📊 Results for Round {selected_round}")

round_data = df[df['Round'] == selected_round]
st.dataframe(round_data)

fig_round = px.bar(
    round_data, 
    x="Candidate", 
    y="Current Round", 
    color="Party", 
    title=f"Votes in Round {selected_round}"
)
st.plotly_chart(fig_round)

# ================================
# 🔸 Vote Progression Over Rounds
# ================================
st.subheader("📈 Vote Progression for Selected Candidates")

if selected_candidates:
    candidate_progress = df[df['Candidate'].isin(selected_candidates)]

    fig_progress = px.line(
        candidate_progress, 
        x="Round", 
        y="Total", 
        color="Candidate", 
        markers=True,
        title="Total Votes Progression Over Rounds"
    )
    st.plotly_chart(fig_progress)
    st.dataframe(candidate_progress)

# ================================
# 🔥 Leading Candidates Per Round
# ================================
st.subheader("🔥 Leading Candidates Per Round")

leading_per_round = df.loc[df.groupby('Round')['Total'].idxmax()]

fig_leading = px.bar(
    leading_per_round,
    x="Round",
    y="Total",
    color="Candidate",
    title="Leading Candidate in Each Round",
    text="Candidate"
)
st.plotly_chart(fig_leading)

st.dataframe(leading_per_round)

# ================================
# 📈 Vote Share Percentage Change
# ================================
st.subheader("📈 Vote Share Percentage Change Over Rounds")

total_votes_per_round = df.groupby('Round')['Total'].sum().reset_index(name='TotalVotes')

df_merged = df.merge(total_votes_per_round, on='Round')
df_merged['VoteSharePercent'] = round(df_merged['Total'] / df_merged['TotalVotes'] * 100, 2)

if selected_candidates:
    filtered = df_merged[df_merged['Candidate'].isin(selected_candidates)]

    fig_share = px.line(
        filtered,
        x="Round",
        y="VoteSharePercent",
        color="Candidate",
        markers=True,
        title="Vote Share Percentage Over Rounds"
    )
    st.plotly_chart(fig_share)
    st.dataframe(filtered)

# ================================
# 🚩 Gain/Loss in Position
# ================================
st.subheader("🚩 Gain/Loss in Position Between Rounds")

df['Rank'] = df.groupby('Round')['Total'].rank(method="min", ascending=False)

position_change = df.pivot_table(
    index='Candidate', 
    columns='Round', 
    values='Rank'
).reset_index()

st.dataframe(position_change)

st.caption("Check how candidates' ranks changed between rounds (lower rank is better).")

fig_rank = px.line(
    df[df['Candidate'].isin(selected_candidates)],
    x="Round",
    y="Rank",
    color="Candidate",
    markers=True,
    title="Rank Change Over Rounds (Lower Rank is Better)",
    line_shape='linear'
)
fig_rank.update_yaxes(autorange="reversed")
st.plotly_chart(fig_rank)
