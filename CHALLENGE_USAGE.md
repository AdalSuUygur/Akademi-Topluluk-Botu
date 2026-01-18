# Challenge Hub Kullanım Kılavuzu

## 📋 Genel Bakış

Challenge Hub, Slack üzerinden mini hackathon'lar düzenlemenizi sağlayan bir sistemdir. Takımlar oluşturup, belirli temalarda projeler geliştirebilirsiniz.

---

## 🚀 Kullanıcı Akışı

### 1. Challenge Başlatma

**Komut:**
```
/challenge start <takım_büyüklüğü> "<tema>" [süre] [zorluk]
```

**Parametreler:**
- `takım_büyüklüğü`: 2-6 arası (zorunlu)
- `tema`: Tırnak içinde (zorunlu)
  - "AI Chatbot"
  - "Web App"
  - "Data Analysis"
  - "Mobile App"
  - "Automation"
- `süre`: Saat cinsinden, 12-168 arası (opsiyonel, varsayılan: 48)
- `zorluk`: beginner, intermediate, advanced (opsiyonel, varsayılan: intermediate)

**Örnekler:**
```
/challenge start 4 "AI Chatbot"
/challenge start 3 "Web App" 72
/challenge start 5 "Data Analysis" 48 "advanced"
```

**Ne Olur:**
1. Challenge oluşturulur
2. Komutun çalıştırıldığı kanala butonlu mesaj gönderilir
3. İlk katılımcı (creator) otomatik eklenir
4. Diğer kullanıcılar butona tıklayarak katılabilir

---

### 2. Challenge'a Katılma

**Yöntem 1: Buton ile (Önerilen)**
- Challenge mesajındaki "🎯 Challenge'a Katıl" butonuna tıklayın
- Otomatik olarak challenge'a katılırsınız

**Yöntem 2: Komut ile**
```
/challenge join
```
- Aktif challenge'a katılır

```
/challenge join <challenge_id>
```
- Belirli challenge'a katılır

**Kısıtlamalar:**
- Aynı challenge'a iki kez katılamazsınız
- Aktif bir challenge'ınız varsa yeni challenge'a katılamazsınız
- Takım dolduysa katılamazsınız

---

### 3. Challenge Durumu

**Komut:**
```
/challenge status
```

**Ne Gösterir:**
- Aktif challenge'ınızın durumu
- Takım büyüklüğü ve katılımcı sayısı
- Challenge kanalı linki
- Süre bilgisi

---

### 4. Challenge Süreci

**Takım Dolduğunda:**
1. Otomatik olarak private challenge kanalı açılır
2. Tüm takım üyeleri kanala eklenir
3. Proje seçilir ve LLM ile özelleştirilir
4. Challenge içeriği kanala gönderilir
5. Süre başlar (örn: 48 saat)

**Challenge Kanalında:**
- Görevler listelenir
- LLM özelleştirmeleri gösterilir
- Kaynaklar paylaşılır
- Takım çalışabilir

**Süre Dolduğunda:**
- Challenge kanalı otomatik kapatılır
- Özet rapor gönderilir

---

## 📝 Örnek Senaryo

### Senaryo: AI Chatbot Challenge

1. **Ali challenge başlatır:**
   ```
   /challenge start 4 "AI Chatbot" 48 intermediate
   ```

2. **Mesaj gönderilir:**
   ```
   🔥 Yeni Challenge Açıldı!
   
   Tema: 🤖 AI Chatbot
   Takım: 4 kişi
   Süre: 48 saat
   Zorluk: Intermediate
   
   [🎯 Challenge'a Katıl] (Buton)
   ```

3. **Ayşe, Mehmet, Zeynep butona tıklar:**
   - Her biri challenge'a katılır
   - Mesaj güncellenir: "Durum: 4/4 kişi"

4. **Takım dolunca:**
   - Private kanal açılır: `#challenge-ai-chatbot-abc123`
   - Proje seçilir: "Eğitim Asistanı Chatbot"
   - LLM özelleştirmeleri eklenir
   - Challenge başlar!

5. **48 saat sonra:**
   - Kanal kapatılır
   - Özet gönderilir

---

## ⚠️ Önemli Notlar

1. **Hub Channel:** Challenge mesajları komutun çalıştırıldığı kanala gönderilir. İsterseniz `#challenge-hub` gibi bir kanal oluşturup orada challenge'ları toplayabilirsiniz.

2. **Aktif Challenge:** Aynı anda sadece bir aktif challenge'ınız olabilir. Yeni challenge başlatmak için önce mevcut challenge'ı tamamlamalısınız.

3. **Tekrar Katılım:** Aynı challenge'a iki kez katılamazsınız (UNIQUE constraint).

4. **Takım Büyüklüğü:** 2-6 kişi arası takım oluşturabilirsiniz.

5. **Süre:** Minimum 12 saat, maksimum 7 gün (168 saat).

---

## 🎯 İpuçları

- Challenge'ları genel bir kanalda (#challenge-hub) toplayın
- Takım büyüklüğünü proje karmaşıklığına göre ayarlayın
- LLM özelleştirmeleri her challenge'a özel özellikler ekler
- Challenge kanalında aktif olun, görevleri paylaşın

---

## 🔧 Sorun Giderme

**Challenge'a katılamıyorum:**
- Aktif challenge'ınız var mı kontrol edin: `/challenge status`
- Takım dolmuş olabilir
- Zaten katıldınız olabilir

**Challenge mesajı görünmüyor:**
- Komutun çalıştırıldığı kanalı kontrol edin
- Bot'un kanala erişimi olduğundan emin olun

**Challenge başlamadı:**
- Takım doldu mu kontrol edin
- Veritabanı hatası olabilir, logları kontrol edin
