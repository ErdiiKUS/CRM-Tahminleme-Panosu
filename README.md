CRM & Tahminleme Panosu (RFM + CLTV + Sepet Analizi)

Bu proje, 'Online Retail II' veri setini kullanarak bir e-ticaret işletmesinin geçmiş satış verilerini analiz eden, gelecek dönem müşteri değerlerini tahminleyen ve sepet analizi ile çapraz satış stratejileri üreten uçtan uca bir veri bilimi ve iş zekası (BI) projesidir.

## 🚀 Proje Mimarisi & Yetkinlikler
- **Veri Temizleme & Hazırlık:** Pandas ve NumPy ile aykırı değer (outlier) analizi, iptal siparişlerin elenmesi ve veri manipülasyonu.
- **Müşteri Segmentasyonu (RFM):** Müşterilerin satın alma sıklığı, yeniliği ve bıraktığı ciroya göre 10 farklı davranışsal segmente ayrılması.
- **Ömür Boyu Değer Tahminleme (CLTV):** `Lifetimes` kütüphanesi kullanılarak **BG/NBD** (Sipariş sayısı tahmini) ve **Gamma-Gamma** (Ortalama sipariş değeri tahmini) modelleriyle gelecek 3 aylık ciro projeksiyonu.
- **Müşteri Kayıp Skoru (Churn):** Her müşterinin anlık sistemde aktif kalma olasılığının (`probability_alive`) olasılıksal modellenmesi.
- **Çapraz Satış (Cross-Sell):** `Mlxtend` kütüphanesi ve **Apriori Algoritması** kullanılarak Birliktelik Kuralları Analizi (Association Rules) ile gelir artırıcı ürün öneri sisteminin kurulması.
- **İş Zekası (Power BI):** Çıkan analitik sonuçların Yıldız Şeması (Star Schema) mimarisiyle interaktif, C-Level yönetim paneline (Executive Summary Dashboard) dönüştürülmesi.

## 📊 Ekran Görüntüleri
*(Buraya Power BI panonun 2009, 2010 ve 2011 yıllarına ait ekran görüntülerini yan yana veya alt alta ekle. Görsel güç çok önemlidir!)*

## 🛠️ Nasıl Çalıştırılır?
1. Gerekli kütüphaneleri yükleyin: `pip install pandas numpy lifetimes mlxtend openpyxl`
2. `main-functions.py` dosyasını çalıştırarak Excel çıktılarını üretin.
3. `CRM-Analisyt.pbit` dosyasını açarak verileri inceleyin.
* Çapraz Satış (Cross-Sell) verisi yıllara göre değil toplam veri seti baz alınarak hesaplanmıştır. 
