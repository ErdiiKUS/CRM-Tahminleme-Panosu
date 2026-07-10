import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import openpyxl as opx
import datetime as dt
import hypothesis as hyp
import pytest as pyt

from PIL.Image import register_extension
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions
from pandas import DataFrame
from pandas.conftest import axis
from pandas.core.groupby import groupby
from pandas.core.interchange import column
from mlxtend.frequent_patterns import apriori, association_rules
from pip._internal.commands import index

pd.set_option('display.max_columns', None)  # Tüm kolonları göster
pd.set_option('display.max_rows', 50)  # Kaç satır göreceğini ayarla
pd.set_option('display.float_format', '{:.2f}'.format)  # Float sayıları 2 ondalıkla göster
pd.set_option('display.width', None)  # Satır genişliği kısıtlamasını kaldır

dataf1 = pd.read_excel("online_retail_II.xlsx", "Year 2009-2010", engine="openpyxl")
dataf2 = pd.read_excel("online_retail_II.xlsx", "Year 2010-2011", engine="openpyxl")
dataf_ = pd.concat([dataf1, dataf2], ignore_index=True)
dataf = dataf_.copy()



#Data info
def check_df(DataFrame, head=5):
    print("####### SHAPE #######") #
    print(DataFrame.shape)
    print("\n####### TYPE #######")
    print(DataFrame.dtypes)
    print("\n####### HEAD #######")
    print(DataFrame.head(head))
    print("\n####### TAIL #######")
    print(DataFrame.tail(head))
    print("\n####### MISSING VALUE #######")
    print(DataFrame.isnull().sum())
    print("\n####### DUBLICATED #######")
    print(DataFrame.duplicated())
    print("\n####### DESCRIBE #######")
    print(DataFrame.describe().T)
    print("\n####### QUANTILES #######")
    print(DataFrame.describe(percentiles=[0, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99, 1]).T)
    print("\n####### UNIQUE VALUES #######")
    print(DataFrame.nunique())
    print("\n####### INFO #######")
    print(DataFrame.info())


check_df(dataf)

#Data temizleme
def clear_data(DataFrame):
    DataFrame.duplicated().sum()
    DataFrame[DataFrame.duplicated(keep=False)].head(20)
    DataFrame = DataFrame.drop_duplicates()
    DataFrame.shape

    # Cancel olan invocice idsinin başında C olan iptal işlemleri veriden temizlendi.
    DataFrame = DataFrame[~DataFrame["Invoice"].astype(str).str.startswith('C')]

    # Price ve Quantity değerleri 0 olan veriler (hatalı, test, kargo vb.) değerlendirilerek  temizlendi.
    DataFrame = DataFrame[(DataFrame["Quantity"] > 0) & (DataFrame["Price"] > 0)]

    # Customer ID si boş olan. Üye olmadan işlem yapılan verileri CRM analizi yapacağımız için temizliyoruz.
    DataFrame = DataFrame.dropna(subset=["Customer ID"])
    DataFrame["Customer ID"] = DataFrame["Customer ID"].astype(int)
    # Tamamen harften oluşan StockCode'ları kontrol edildi ve Test dataları temizlendi.
    stock_clear = DataFrame[DataFrame["StockCode"].astype(str).str.match(r'^[A-Za-z]+$')]["StockCode"].value_counts()
    DataFrame = DataFrame[~DataFrame["StockCode"].astype(str).isin(stock_clear.index)]
    return DataFrame


dataf = clear_data(dataf)


#RFM rapor
def rfm_process (DataFrame):
    DataFrame["InvoiceDate"] = pd.to_datetime(DataFrame["InvoiceDate"])
    reference_date = DataFrame["InvoiceDate"].max() + pd.Timedelta(days=1)
    DataFrame["TotalRevenue"] = DataFrame["Quantity"] * DataFrame["Price"]

    rfm = DataFrame.groupby("Customer ID").agg(
        Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
        Frequency=('Invoice', 'nunique'),
        Monetary=('TotalRevenue', 'sum'),
    ).reset_index()

    # Hazırladığım RFM metriklerini segmente ettim.
    rfm["RecencyScore"] = pd.qcut(rfm["Recency"], 5, [5, 4, 3, 2, 1])
    rfm["FrequencyScore"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, [1, 2, 3, 4, 5])
    rfm["MonetaryScore"] = pd.qcut(rfm["Monetary"], 5, [1, 2, 3, 4, 5])

    # Oluşan segment değerlerinden RFM ve RF değerlerini hesapladım.
    rfm["RFM"] = rfm["RecencyScore"].astype(str) + rfm["FrequencyScore"].astype(str) + rfm["MonetaryScore"].astype(str)
    rfm["RF"] = rfm["RecencyScore"].astype(str) + rfm["FrequencyScore"].astype(str)

    # Segment tablosunu tanımlama
    seg_map = {
        r'[1-2][1-2]': 'Hibernating',
        r'[1-2][3-4]': 'At Risk',
        r'[1-2]5': 'Cant Lose Them',
        r'3[1-2]': 'About to Sleep',
        r'33': 'Need Attention',
        r'[3-4][4-5]': 'Loyal Customers',
        r'41': 'Promising',
        r'51': 'New Customers',
        r'[4-5][2-3]': 'Potential Loyalists',
        r'5[4-5]': 'Champions'
    }

    # Segment değerine referans alınarak datalar site_map göre isimlendirildi.
    rfm["Segment"] = rfm["RF"].astype(str).replace(seg_map, regex=True)
    rfm["Segment"].value_counts()

    # RFM analizindeki RFM ve RF değerlerinin data tablosuna aktarımını yaptım.
    rfm["Customer ID"] = rfm["Customer ID"].astype(int)
    rfm_transfer_data = rfm[["Customer ID", "RFM", "RF", "Segment"]]

    rfm_export = pd.merge(DataFrame, rfm_transfer_data, on="Customer ID", how="left")
    rfm_export.to_excel("RFM.xlsx", index=False)
    print("Completed RFM")
    return rfm_export


dataf = rfm_process (dataf)




#CLTV

def outlier_thresholds(DataFrame, variable ):
    quantile1 = (DataFrame[variable].quantile(0.01))
    quantile3 = (DataFrame[variable].quantile(0.99))
    interquantile_range = quantile3 - quantile1
    up_limit = quantile3 + 1.5 * interquantile_range
    low_limit = quantile1 - 1.5 * interquantile_range
    return  low_limit, up_limit

def replace_with_thresholds (DataFrame, variable):
    low_limit, up_limit = outlier_thresholds(DataFrame, variable)
    DataFrame.loc[(DataFrame[variable] < low_limit), variable] = round(low_limit)
    DataFrame.loc[(DataFrame[variable] > up_limit), variable] = round(up_limit)

def cltv_process(DataFrame):
    temp_df = DataFrame.groupby("Customer ID").agg(
        last_order_date=("InvoiceDate", "max"),
        first_order_date=("InvoiceDate", "min"),
        order_num_total=("Invoice", "nunique"),
        customer_total_value=("TotalRevenue", "sum")
    ).reset_index()

    reference_date = DataFrame["InvoiceDate"].max() + pd.Timedelta(days=1)

    cltv_df = pd.DataFrame()
    cltv_df["Customer ID"] = temp_df["Customer ID"]
    cltv_df["Recency"] = (temp_df["last_order_date"] - temp_df["first_order_date"]).dt.days / 7
    cltv_df["Frequency"] = temp_df["order_num_total"]
    cltv_df["Monetary"] = temp_df["customer_total_value"] / temp_df["order_num_total"]
    cltv_df["T"] = (reference_date - temp_df["first_order_date"]).dt.days / 7

    cltv_df = cltv_df[cltv_df["Frequency"] > 1].reset_index()

    replace_with_thresholds(cltv_df, "Frequency")
    replace_with_thresholds(cltv_df, "Monetary")

    bgf = BetaGeoFitter(penalizer_coef=0.001)
    bgf.fit(cltv_df["Frequency"],
            cltv_df["Recency"],
            cltv_df["T"]
            )

    cltv_df["probability_alive"] = bgf.conditional_probability_alive(cltv_df["Frequency"], cltv_df["Recency"],
                                                                     cltv_df["T"])

    cltv_df["3_month_order"] = bgf.conditional_expected_number_of_purchases_up_to_time(52 / 4,
                                                                                       cltv_df["Frequency"],
                                                                                       cltv_df["Recency"],
                                                                                       cltv_df["T"])

    ggf = GammaGammaFitter(penalizer_coef=0.001)
    ggf.fit(cltv_df["Frequency"],
            cltv_df["Monetary"]
            )

    cltv_df["3_month_value"] = ggf.customer_lifetime_value(bgf,
                                                           cltv_df["Frequency"],
                                                           cltv_df["Recency"],
                                                           cltv_df["T"],
                                                           cltv_df["Monetary"],
                                                           time=52 / 4,
                                                           discount_rate=0.01,
                                                           freq="W")

    cltv_df.sort_values("3_month_value", ascending=False)
    cltv_df["CLTV_Segment"] = pd.qcut(cltv_df["3_month_value"], 4, ["D","C","B","A"])
    cltv_df.to_excel("CLTV.xlsx", index=False)

    RFM_CLTV = pd.merge(
        DataFrame,
        cltv_df[["Customer ID", "probability_alive", "3_month_order", "3_month_value", "CLTV_Segment"]],
        on="Customer ID",
        how="left"
    )

    RFM_CLTV.to_excel("RFM_CLTV.xlsx", index=False)
    print("Completed CLTV")
    return RFM_CLTV




RFM_CLTV = cltv_process(dataf)


#Cross-Sell

def cross_sell_items(DataFrame):

    invoice_product_df = (DataFrame[DataFrame["Quantity"] > 0]
                          .groupby(["Invoice", "StockCode"])["Quantity"]
                          .sum()
                          .unstack()
                          .fillna(0)
                          .map(lambda x: 1 if x > 0 else 0))

    frequnent_itemsets = apriori(invoice_product_df, min_support=0.02, use_colnames=True)
    rules = association_rules(frequnent_itemsets, metric="lift", min_threshold=1)
    rules = rules.sort_values(by="lift", ascending=False)

    rules["antecedents"] = rules["antecedents"].apply(lambda x: list(x)[0]).astype(str)
    rules["consequents"] = rules["consequents"].apply(lambda x: list(x)[0]).astype(str)

    cross_sell_df = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
    cross_sell_df.to_excel("cross_sell_onerileri.xlsx", index=False)
    print("Cross-Sell tablosu başarıyla kaydedildi!")
    return cross_sell_df





Cross_sellItem = cross_sell_items(RFM_CLTV)



