CREATE TABLE IF NOT EXISTS tours (
  id SERIAL PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title JSONB NOT NULL,        -- {"ky":"","en":"","ru":"","es":""}
  description JSONB NOT NULL,
  days INT NOT NULL,
  price_usd INT NOT NULL,
  region TEXT,
  color TEXT DEFAULT '#0E3B4F',
  active BOOLEAN DEFAULT true
);
CREATE TABLE IF NOT EXISTS bookings (
  id SERIAL PRIMARY KEY,
  tour_id INT NOT NULL REFERENCES tours(id),
  name TEXT NOT NULL,
  contact TEXT NOT NULL,
  start_date DATE,
  people INT DEFAULT 1,
  comment TEXT,
  lang TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO tours (slug,title,description,days,price_usd,region,color) VALUES
('issyk-kul',
 '{"ky":"Ысык-Көл айланасы","en":"Issyk-Kul Lake Loop","ru":"Кольцо вокруг Иссык-Куля","es":"Vuelta al lago Issyk-Kul"}',
 '{"ky":"Дүйнөдөгү эң чоң тоо көлдөрүнүн бири: пляждар, кайнар суулар, жайлоолор.","en":"One of the largest alpine lakes on Earth: beaches, hot springs and summer pastures.","ru":"Одно из крупнейших горных озёр мира: пляжи, термальные источники, джайлоо.","es":"Uno de los mayores lagos de montaña del mundo: playas, aguas termales y pastos de verano."}',
 5,420,'Issyk-Kul','#0E3B4F'),
('song-kol',
 '{"ky":"Сон-Көл жайлоосу","en":"Song-Kol Yurt Stay","ru":"Ночёвка в юртах на Сон-Куле","es":"Noche en yurta en Song-Kol"}',
 '{"ky":"3000 м бийиктикте юрта, ат минүү жана жылдыздуу асман.","en":"Yurts at 3,000 m, horse riding and a sky full of stars.","ru":"Юрты на высоте 3000 м, конные прогулки и звёздное небо.","es":"Yurtas a 3.000 m, paseos a caballo y un cielo lleno de estrellas."}',
 3,260,'Naryn','#2F5D4A'),
('ala-kul',
 '{"ky":"Ала-Көл треки","en":"Ala-Kul Trek","ru":"Трек на Ала-Куль","es":"Trekking a Ala-Kul"}',
 '{"ky":"Каракол капчыгайынан Ала-Көл ашуусуна чейинки популярдуу жол.","en":"The classic route from Karakol gorge over the Ala-Kul pass.","ru":"Классический маршрут из ущелья Каракол через перевал Ала-Куль.","es":"La ruta clásica desde el desfiladero de Karakol por el paso de Ala-Kul."}',
 4,350,'Karakol','#7A3B2E'),
('jeti-oguz',
 '{"ky":"Жети-Өгүз жана Жомок","en":"Jeti-Oguz & Fairytale Canyon","ru":"Джеты-Огуз и Сказка","es":"Jeti-Oguz y Cañón del Cuento"}',
 '{"ky":"Кызыл аска жана Жомок капчыгайы — эки күндүк жеңил саякат.","en":"Red rocks and a canyon of strange shapes: an easy two-day trip.","ru":"Красные скалы и каньон причудливых форм: лёгкая поездка на два дня.","es":"Rocas rojas y un cañón de formas extrañas: un viaje fácil de dos días."}',
 2,150,'Issyk-Kul','#B5622F')
ON CONFLICT (slug) DO NOTHING;
