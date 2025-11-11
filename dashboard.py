import streamlit as st
import pandas as pd
import plotly.express as px

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Analisis Penjualan Sederhana",
    layout="wide"
)

# --- Judul Dashboard ---
st.title("🛍️ Dashboard Analisis Penjualan")
st.markdown("Analisis Tren Penjualan, Pola Pembelian, dan Metode Pembayaran")
st.divider()

# --- Fungsi Muat Data ---
# Asumsikan data Anda disimpan dalam file CSV
@st.cache_data
def load_data(file_path):
    try:
        # Ganti dengan nama file Anda yang sebenarnya
        df = pd.read_csv(file_path)
        
        # Konversi tipe data sesuai deskripsi gambar
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        df['signup_date'] = pd.to_datetime(df['signup_date'], errors='coerce')
        
        # Pastikan kolom total_sales numerik
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
        
        # Hapus baris dengan nilai NA di kolom penting untuk analisis
        df.dropna(subset=['order_date', 'total_sales', 'country', 'category', 'payment_method'], inplace=True)
        
        return df
    except FileNotFoundError:
        st.error(f"File **{file_path}** tidak ditemukan. Pastikan file data Anda ada.")
        st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        st.stop()

# Ganti 'data_penjualan.csv' dengan nama file Anda
data_path = 'cleandata.csv'
df = load_data(data_path)

# --- Filter Samping Global (Opsional) ---
st.sidebar.header("Filter Analisis")
year_filter = st.sidebar.multiselect(
    'Pilih Tahun',
    options=sorted(df['order_date'].dt.year.unique(), reverse=True),
    default=sorted(df['order_date'].dt.year.unique())
)

df_filtered = df[df['order_date'].dt.year.isin(year_filter)]

if df_filtered.empty:
    st.warning("Tidak ada data untuk tahun yang dipilih.")
    st.stop()

# --- 1. Perbandingan Nilai Penjualan ---
st.header("📊 1. Perbandingan Nilai Penjualan (Total Sales)")
col1, col2, col3 = st.columns(3)

# 1.1 Penjualan per Negara
sales_by_country = df_filtered.groupby('country')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False).head(10)
fig_country = px.bar(
    sales_by_country, 
    x='country', 
    y='total_sales', 
    title="Top 10 Negara Berdasarkan Total Penjualan",
    color_discrete_sequence=px.colors.qualitative.T10
)
col1.plotly_chart(fig_country, use_container_width=True)

# 1.2 Penjualan per Kategori Produk
sales_by_category = df_filtered.groupby('category')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False)
fig_category = px.pie(
    sales_by_category, 
    values='total_sales', 
    names='category', 
    title="Distribusi Penjualan per Kategori Produk"
)
col2.plotly_chart(fig_category, use_container_width=True)

# 1.3 Penjualan per Metode Pembayaran
sales_by_payment = df_filtered.groupby('payment_method')['total_sales'].sum().reset_index().sort_values(by='total_sales', ascending=False)
fig_payment = px.bar(
    sales_by_payment, 
    x='payment_method', 
    y='total_sales', 
    title="Penjualan per Metode Pembayaran",
    color_discrete_sequence=px.colors.qualitative.T10
)
col3.plotly_chart(fig_payment, use_container_width=True)

st.divider()

# --- 2. Pola Pembelian dan Frekuensi Metode Pembayaran ---
st.header("🛒 2. Pola Pembelian dan Frekuensi Pembayaran")
col4, col5 = st.columns(2)

# 2.1 Pola Pembelian: Gender vs Kategori Barang (Count/Frekuensi)
gender_category = df_filtered.groupby(['gender', 'category']).size().reset_index(name='order_count')
fig_gender_cat = px.bar(
    gender_category,
    x='category',
    y='order_count',
    color='gender',
    title="Frekuensi Pembelian per Kategori Berdasarkan Gender",
    barmode='group'
)
col4.plotly_chart(fig_gender_cat, use_container_width=True)

# 2.2 Metode Pembayaran Paling Sering Digunakan (Frekuensi)
freq_payment = df_filtered['payment_method'].value_counts().reset_index()
freq_payment.columns = ['payment_method', 'order_count']
fig_freq_payment = px.bar(
    freq_payment,
    x='payment_method',
    y='order_count',
    title="Metode Pembayaran Paling Sering Digunakan (Frekuensi Transaksi)",
    color_discrete_sequence=px.colors.qualitative.G10
)
col5.plotly_chart(fig_freq_payment, use_container_width=True)

st.divider()

# --- 3. Tren Penjualan Berdasarkan Waktu ---
st.header("📈 3. Tren Penjualan Seiring Waktu")

time_option = st.radio(
    "Pilih Periode Waktu Tren:",
    ('Bulanan', 'Tahunan'),
    horizontal=True
)

if time_option == 'Tahunan':
    df_trend = df_filtered.set_index('order_date').resample('Y')['total_sales'].sum().reset_index()
    df_trend['Period'] = df_trend['order_date'].dt.to_period('Y').astype(str)
elif time_option == 'Bulanan':
    df_trend = df_filtered.set_index('order_date').resample('M')['total_sales'].sum().reset_index()
    df_trend['Period'] = df_trend['order_date'].dt.to_period('M').astype(str)

fig_time_trend = px.line(
    df_trend, 
    x='Period', 
    y='total_sales', 
    title=f"Tren Total Penjualan ({time_option})",
    markers=True
)
st.plotly_chart(fig_time_trend, use_container_width=True)

st.subheader("Tren Penjualan Detail: Produk & Kategori")

col6, col7 = st.columns(2)

# 3.1 Tren Penjualan per Kategori
if time_option == 'Tahunan':
    category_trend = df_filtered.groupby([df_filtered['order_date'].dt.to_period('Y'), 'category'])['total_sales'].sum().reset_index()
    category_trend.columns = ['Period', 'category', 'total_sales']
    category_trend['Period'] = category_trend['Period'].astype(str)
elif time_option == 'Bulanan':
    category_trend = df_filtered.groupby([df_filtered['order_date'].dt.to_period('M'), 'category'])['total_sales'].sum().reset_index()
    category_trend.columns = ['Period', 'category', 'total_sales']
    category_trend['Period'] = category_trend['Period'].astype(str)

fig_cat_trend = px.line(
    category_trend, 
    x='Period', 
    y='total_sales', 
    color='category', 
    title=f"Tren Penjualan Kategori ({time_option})",
    markers=True
)
col6.plotly_chart(fig_cat_trend, use_container_width=True)


# 3.2 Top 5 Produk Tren (Sebagai Contoh)
# Mendapatkan 5 produk teratas berdasarkan total penjualan
top_products = df_filtered.groupby('product_name')['total_sales'].sum().nlargest(5).index

# Filter data hanya untuk 5 produk teratas
df_top_products = df_filtered[df_filtered['product_name'].isin(top_products)]

if time_option == 'Tahunan':
    product_trend = df_top_products.groupby([df_top_products['order_date'].dt.to_period('Y'), 'product_name'])['total_sales'].sum().reset_index()
    product_trend.columns = ['Period', 'product_name', 'total_sales']
    product_trend['Period'] = product_trend['Period'].astype(str)
elif time_option == 'Bulanan':
    product_trend = df_top_products.groupby([df_top_products['order_date'].dt.to_period('M'), 'product_name'])['total_sales'].sum().reset_index()
    product_trend.columns = ['Period', 'product_name', 'total_sales']
    product_trend['Period'] = product_trend['Period'].astype(str)

fig_prod_trend = px.line(
    product_trend, 
    x='Period', 
    y='total_sales', 
    color='product_name', 
    title=f"Tren Penjualan Top 5 Produk ({time_option})",
    markers=True
)
col7.plotly_chart(fig_prod_trend, use_container_width=True)

st.markdown("---")
st.caption(f"Data diproses dari file: **{data_path}**")