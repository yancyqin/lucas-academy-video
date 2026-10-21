# 德彪西 × 印象派 音乐影片 — 曲子和画的清单 v0.1（2026-10-13）

预览页（带缩略图和试听）：`lucas-academy-video-data/debussy-impressions/preview/index.html`，同时发布为 Claude 页面（见会话）。本文件由 `scripts/debussy-impressions/build_preview.py` 从 `lucas-academy-video-data/debussy-impressions/{program.json, paintings.json, music/sources.json}` 生成，改数据再跑脚本，不要手改表格。

## 1. 概念和镜头语言

- 每幅画：**写实还原（Codex 生成的照片感画面）→ 慢慢溶成印象派成品 → 定格 → 换下一幅**。溶的过程就是片子的内容：观众看着照片变成画。
- 每首曲子一组画。画的切换跟着乐句的起点走（和巴赫组曲一样的规矩）；慢的曲子画少、每幅停得久，不在慢乐段里赶画。
- 鲁昂大教堂那一组只需要一张写实照片：同一机位依次溶入清晨、阴天、上午、正午、下午、日落六幅莫奈，画面本身就在讲“光变了，墙没变”。
- 全片不用 AI 生成的音乐；写实还原是 AI 生成的图，按惯例标注“AI 生成”。
- 结尾：焰火定格到黑；按片尾规矩留一句开放的问题（待写）。

## 2. 录音许可和音量

所有录音统一到 −18 LUFS（真峰值 ≤ −1 dBTP），只用整体增益，不压缩曲子内部的强弱；峰值超出的几首用 192 kHz 过采样的限幅器削峰，限幅器最多只在 2.6% 的时间里起作用。

只用公有领域（必须在美国也过期：美国政府作品、1923 年前出版的录音）、CC0、CC BY（简介里署名）。BY-SA、NC、ND、Free Art License 不用。IMSLP 上标 “Public Domain – Non-PD US” 的名家老录音不用。维基共享资源上 Marcelle Meyer 1956–57 的整套前奏曲和意象集虽然挂着 PD 标签，但美国要到 2066 年以后才过期，不用。

## 3. 正片顺序（六首，约 32:48）

一天的弧线：雾中的教堂 → 水 → 雪 → 舞 → 夜 → 焰火。觉得长就先去掉《雪上足迹》和《世俗舞曲》，剩四首约 23 分钟。

### 1. 沉没的教堂 · La cathédrale engloutie

《前奏曲》第一集第 10 首，1910。音乐从雾里浮起、钟声大作、再沉回水底；莫奈的鲁昂大教堂系列正好是同一面墙在一天里的变化。全组只需一张写实照片，依次溶入六幅画。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| La cathédrale engloutie (Préludes I/10) | Ivan Ilić, piano (Paris, April 2006) | CC BY 3.0 — credit required | 5:25 | [来源](https://commons.wikimedia.org/wiki/File:La_Cath%C3%A9drale_engloutie_-_Claude_Debussy_-_performed_by_Ivan_Ilic.ogg) · 本地 `candidates/cathedrale-engloutie-ilic-ccby3.ogg` · Professional pianist; OTRS permission ticket on Commons. ogg 160 kbps, nothing above 15 kHz. |
| La cathédrale engloutie (Préludes I/10) — alternative | Stefano Ligoratti, piano (live) | CC BY 3.0 — credit required | 5:51 | [来源](https://imslp.org/wiki/Special:ImagefromIndex/220924) · 本地 `candidates/cathedrale-ligoratti-ccby3.mp3` · Live. 40 clipped runs in the original, MP3 cut at 14 kHz — Ilić is cleaner. Got the file from the Wayback Machine copy of the IMSLP file (2015-09-28). |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门（清晨效果） Rouen Cathedral, the Portal (Morning Effect) | 1894 | 巴塞尔贝耶勒基金会 Fondation Beyeler | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Rouen_Cathedral%2C_Facade_%28Morning_effect%29.JPG) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Rouen_Cathedral%2C_Facade_%28Morning_effect%29.JPG) | 整组只需要一张写实照片：鲁昂大教堂西立面，从对面二楼窗口（莫奈租的房间）平视。清晨，雾还没散，石头几乎没有颜色。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门，阴天 The Portal, Grey Weather | 1892 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Cathedral_in_Rouen._The_portal%2C_Grey_Weather_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Cathedral_in_Rouen._The_portal%2C_Grey_Weather_-_Google_Art_Project.jpg) | 同一机位，阴天漫射光，灰蓝。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门与圣罗曼塔，晨光（蓝色和谐） Harmonie bleue | 1893 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_033.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_033.jpg) | 同一机位，上午斜射的阳光刚碰到塔顶。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂西立面，阳光 West Façade, Sunlight | 1894 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_Rouen_Cathedral%2C_West_Fa%C3%A7ade%2C_Sunlight%2C_1894%2C_NGA_46654.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_Rouen_Cathedral%2C_West_Fa%C3%A7ade%2C_Sunlight%2C_1894%2C_NGA_46654.jpg) | 同一机位，正午前后，立面被晒成金色，门洞里是蓝紫色的影子。音乐在此处最响（钟声/管风琴）。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门与圣罗曼塔，全日照（蓝与金的和谐） Harmonie bleue et or | 1893 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Cath%C3%A9drale_de_Rouen._Harmonie_bleue_et_or.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Cath%C3%A9drale_de_Rouen._Harmonie_bleue_et_or.jpg) | 同一机位，下午。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门（日落） Façade (Sunset) | 1892–94 | 巴黎玛摩丹莫奈博物馆 Musée Marmottan Monet | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Rouen_Cathedral%2C_Facade_%28Sunset%29.JPG) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Rouen_Cathedral%2C_Facade_%28Sunset%29.JPG) | 同一机位，日落，石头变成橙红和紫色。教堂沉回水底。 |
| 克劳德·莫奈 Claude Monet | 鲁昂大教堂：正门（阳光） Rouen Cathedral: The Portal (Sunlight) | 1894 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Rouen_Cathedral-_The_Portal_%28Sunlight%29_MET_DT2185.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Rouen_Cathedral-_The_Portal_%28Sunlight%29_MET_DT2185.jpg) | 同一面西立面，阳光照在正门和左侧塔楼上，石头偏暖白，阴影是蓝紫。 |
| 克劳德·莫奈 Claude Monet | 晨光中的鲁昂大教堂正门 The Portal of Rouen Cathedral in Morning Light | 1894 | 洛杉矶盖蒂美术馆 J. Paul Getty Museum（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Portal_of_Rouen_Cathedral_in_Morning_Light_%281894%29_-_Getty_Center_2001.33.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Portal_of_Rouen_Cathedral_in_Morning_Light_%281894%29_-_Getty_Center_2001.33.jpg) | 早晨，雾刚散，阳光从侧面照亮立面上部，下部还在蓝色阴影里。 |


### 2. 水：睡莲 · Reflets dans l'eau → 弦乐四重奏第三乐章

《意象集》第一集第 1 首，1905 / 弦乐四重奏 Op.10 第三乐章，1893。《水中倒影》是最该配睡莲的曲子，但没找到可用的录音（见文末）。先用弦乐四重奏慢乐章顶上：同样安静、漂浮，8 分钟够三幅睡莲各停很久。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| String Quartet in G minor, Op. 10 — III. Andantino, doucement expressif | Euclid Quartet (Indiana University South Bend) | CC BY (YouTube Creative Commons licence) — credit required | 7:59 | [来源](https://commons.wikimedia.org/wiki/File:Debussy_-_String_Quartet_in_G_Minor_-_III._Andantino,_doucement_expressif_(Euclid_Quartet).opus) · 本地 `candidates/quartet-3-andantino-euclid-ccby.opus` |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 睡莲 Water Lilies | 1906 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Water_Lilies_-_1933.1157_-_Art_Institute_of_Chicago.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Water_Lilies_-_1933.1157_-_Art_Institute_of_Chicago.jpg) | 吉维尼睡莲池的一小块水面：没有地平线，只有睡莲、天空和柳树的倒影。 |
| 克劳德·莫奈 Claude Monet | 睡莲池上的桥 Bridge over a Pond of Water Lilies | 1899 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg) | 吉维尼的日本桥，夏天，绿色主调，桥下满是睡莲。 |
| 克劳德·莫奈 Claude Monet | 日本桥 The Japanese Footbridge | 1899 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_The_Japanese_Footbridge%2C_1899%2C_NGA_74796.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_The_Japanese_Footbridge%2C_1899%2C_NGA_74796.jpg) | 同一座桥，稍微换个角度，紫藤和光更多。 |


### 3. 雪上足迹 · Des pas sur la neige

《前奏曲》第一集第 6 首，1910。一步一步的固定音型，配雪景：喜鹊、西斯莱的雪路、雪中屋顶、雪地里的麦垛日落。两版录音：Bertoglio 更干净（正片用），Baldaccini 安静段有沙沙声，演奏风格可以比一比。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Des pas sur la neige (Préludes I/6) | Chiara Bertoglio, piano | CC BY 3.0 — credit required | 4:01 | [来源](https://imslp.org/wiki/Special:ImagefromIndex/297337) · 本地 `candidates/neige-bertoglio-ccby3.mp3` · Recorded very quietly (−36 LUFS); after normalizing, hiss in the quietest passages is about −75 dBFS above 8 kHz, inaudible. Wayback copy of the IMSLP file (2022-04-20). |
| Des pas sur la neige (Préludes I/6) — alternative | Ilaria Baldaccini, piano (Florence Conservatory graduate) | Public domain (Musopen) | 4:02 | [来源](https://musopen.org/music/4509-preludes-book-1/) · 本地 `candidates/neige-baldaccini-pd.mp3` · Musopen download 2026-10-14, 128 kbps from an MP4 source. Noisier than Bertoglio: hiss about −57 dBFS above 8 kHz in the quietest passages after normalizing, against −75 for Bertoglio. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 喜鹊 The Magpie | 1868–69 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Magpie_-_Google_Art_Project.jpg) | 埃特勒塔附近雪后清晨，篱笆门上停着一只喜鹊，雪地上拖着长长的蓝影，天空淡黄。 |
| 阿尔弗雷德·西斯莱 Alfred Sisley | 卢沃谢讷的雪 Snow at Louveciennes | 1878 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Alfred_Sisley_-_Snow_at_Louveciennes_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Alfred_Sisley_-_Snow_at_Louveciennes_-_Google_Art_Project.jpg) | 卢沃谢讷村的积雪小路，木栅栏夹道，远处一个撑伞的行人，雪还在下。 |
| 古斯塔夫·卡耶博特 Gustave Caillebotte | 雪中的屋顶 Rooftops in the Snow | 1878 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Gustave_Caillebotte_-_Rooftops_in_the_Snow_%28snow_effect%29_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Gustave_Caillebotte_-_Rooftops_in_the_Snow_%28snow_effect%29_-_Google_Art_Project.jpg) | 从巴黎公寓高层窗口俯瞰，雪盖住锌皮屋顶和烟囱，灰白的天。 |
| 克劳德·莫奈 Claude Monet | 麦垛（日落，雪景） Stacks of Wheat (Sunset, Snow Effect) | 1890–91 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Stacks_of_Wheat_%28Sunset%2C_Snow_Effect%29_-_1922.431_-_Art_Institute_of_Chicago.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Stacks_of_Wheat_%28Sunset%2C_Snow_Effect%29_-_1922.431_-_Art_Institute_of_Chicago.jpg) | 吉维尼田里两个麦垛，雪地，落日逆光，影子拉向观众。 |


### 4. 世俗舞曲 · Danse profane

《神圣与世俗舞曲》（竖琴与弦乐），1904。竖琴的华尔兹，配雷诺阿的四幅舞蹈：布吉瓦尔、乡村、城市、煎饼磨坊。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Danse profane (Danses pour harpe et orchestre, 2) | United States Marine Chamber Orchestra, cond. Jason K. Fettig, harp Karen Grimsey (live, 14 Aug 2010) | Public domain (US government work) | 5:40 | [来源](https://commons.wikimedia.org/wiki/File:Danse_Profane.ogg) · 本地 `candidates/danse-profane-usmc-pd.ogg` · Live concert; the published track ends on the final chord, no audible applause in the last 5 s (−41 dB mean) — confirm by ear before cutting. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 布吉瓦尔之舞 Dance at Bougival | 1883 | 波士顿美术馆 Museum of Fine Arts, Boston | [Commons](https://commons.wikimedia.org/wiki/File:Dance-At-Bougival.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Dance-At-Bougival.jpg) | 塞纳河畔布吉瓦尔的露天舞会，戴红帽的女子和戴草帽的男子贴身跳舞，地上落着花。 |
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 乡村之舞 Dance in the Country | 1883 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Pierre_Auguste_Renoir_-_Country_Dance_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Pierre_Auguste_Renoir_-_Country_Dance_-_Google_Art_Project.jpg) | 乡间餐馆的露台，栗树下，女子回头对观众笑，桌上还有没吃完的饭。 |
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 城市之舞 Dance in the City | 1883 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Danse_%C3%A0_la_ville_%28Pierre-Auguste_Renoir%29-WUS07474.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Danse_%C3%A0_la_ville_%28Pierre-Auguste_Renoir%29-WUS07474.jpg) | 舞厅里的一对：白色长裙、黑色燕尾服，背景是棕榈。和《乡村之舞》是一对。 |
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 煎饼磨坊的舞会 Bal du moulin de la Galette | 1876 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Pierre-Auguste_Renoir%2C_Le_Moulin_de_la_Galette.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Auguste_Renoir_-_Dance_at_Le_Moulin_de_la_Galette_-_Google_Art_ProjectFXD.jpg) | 蒙马特的露天舞场，周日下午，树影斑斑点点落在人群身上。 |


### 5. 月光 · Clair de lune

《贝加莫组曲》第 3 首，1905 出版。夜景三幅：毕沙罗的雨夜大道、梵高的罗讷河星夜、惠斯勒的蓝金夜曲。德彪西的管弦乐《夜曲》就是以惠斯勒的 Nocturne 命名的，可以写进简介。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Clair de lune (Suite bergamasque, III) | Laurens Goedhart, piano (2011) | CC BY 3.0 — credit required (composition PD) | 5:04 | [来源](https://commons.wikimedia.org/wiki/File:Clair_de_lune_(Claude_Debussy)_Suite_bergamasque.ogg) · 本地 `candidates/clair-de-lune-goedhart-ccby3.ogg` · ogg 500 kbps transcoded from a SoundCloud MP3: nothing above 15 kHz. Clean lead-in. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 卡米耶·毕沙罗 Camille Pissarro | 夜晚的蒙马特大道 The Boulevard Montmartre at Night | 1897 | 伦敦国家美术馆 National Gallery, London | [Commons](https://commons.wikimedia.org/wiki/File:Camille_Pissarro_-_Boulevard_Montmartre_at_Night_-_c_1897_-_National_Gallery_UK.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Camille_Pissarro_-_Boulevard_Montmartre_at_Night_-_c_1897_-_National_Gallery_UK.jpg) | 巴黎蒙马特大道，雨后夜晚，从俄罗斯饭店楼上俯瞰：街灯、橱窗和马车灯倒映在湿漉漉的路面上。 |
| 文森特·梵高 Vincent van Gogh | 罗讷河上的星夜 Starry Night Over the Rhône | 1888 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Starry_Night_Over_the_Rhone.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Starry_Night_Over_the_Rhone.jpg) | 阿尔勒罗讷河岸，夜里煤气灯在水面拉出金色竖纹，天上是北斗七星，岸边一对散步的人。后印象派。 |
| 詹姆斯·惠斯勒 James McNeill Whistler | 蓝与金的夜曲：旧巴特西桥 Nocturne: Blue and Gold – Old Battersea Bridge | 约 1872–75 | 伦敦泰特美术馆 Tate Britain | [Commons](https://commons.wikimedia.org/wiki/File:James_McNeill_Whistler_-_Nocturne_en_bleu_et_or.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/James_McNeill_Whistler_-_Nocturne_en_bleu_et_or.jpg) | 泰晤士河上的旧巴特西木桥，蓝雾夜色，船夫撑船穿过高高的桥墩，远处一点焰火。德彪西的管弦乐《夜曲》就是以惠斯勒的这组 Nocturne 命名的。 |
| 文森特·梵高 Vincent van Gogh | 星夜 The Starry Night（备选） | 1889 | 纽约现代艺术博物馆 MoMA | [Commons](https://commons.wikimedia.org/wiki/File:Vincent_van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Vincent_van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg) | 圣雷米疗养院窗外的夜空与村庄，柏树在前景。更有名，但更“表现”而不是“印象”，列为备选。 |


### 6. 焰火 · Feux d'artifice

《前奏曲》第二集第 12 首，1913。收尾。惠斯勒的《坠落的火箭》定格到底；曲子结尾远远飘来《马赛曲》，正好切到莫奈的国庆日旗海。录音是 Ligoratti 的现场版，结尾没有掌声。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Feux d'artifice (Préludes II/12) | Stefano Ligoratti, piano (live) | CC BY 3.0 — credit required | 4:39 | [来源](https://imslp.org/wiki/Special:ImagefromIndex/220928) · 本地 `candidates/feux-ligoratti-ccby3.mp3` · Live; no applause in the tail. 26 short clipped runs in the original master, MP3 cut at 14.5 kHz. Wayback copy of the IMSLP file (2023-09-29). |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 詹姆斯·惠斯勒 James McNeill Whistler | 黑与金的夜曲：坠落的火箭 Nocturne in Black and Gold – The Falling Rocket | 1875 | 底特律美术馆 Detroit Institute of Arts | [Commons](https://commons.wikimedia.org/wiki/File:Whistler-Nocturne_in_black_and_gold.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Whistler-Nocturne_in_black_and_gold.jpg) | 伦敦克里莫恩游乐园的夜间焰火，一枚火箭落下来的金色火花。当年罗斯金骂它是“把一罐颜料泼在公众脸上”。 |
| 克劳德·莫奈 Claude Monet | 蒙托格伊街，1878 年 6 月 30 日节日 The Rue Montorgueil, Celebration of 30 June 1878 | 1878 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Rue_Montorgueil_in_Paris._Celebration_of_June_30%2C_1878_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Rue_Montorgueil_in_Paris._Celebration_of_June_30%2C_1878_-_Google_Art_Project.jpg) | 从楼上俯视，整条街挂满三色旗，底下是人潮。《焰火》结尾远远引用了《马赛曲》，正是这个节日。 |
| 克劳德·莫奈 Claude Monet | 圣德尼街，1878 年 6 月 30 日节日 Rue Saint-Denis, Celebration of 30 June 1878 | 1878 | 鲁昂美术馆 Musée des Beaux-Arts de Rouen | [Commons](https://commons.wikimedia.org/wiki/File:Rouen_%28Seine-Maritime%29_-_Mus%C3%A9e_des_Beaux-Arts_-_%22Rue_Saint-Denis%2C_F%C3%AAte_du_30_juin_1878%22_%28Claude_Monet%2C_1840-1926%29_%2832758484702%29.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Rouen_%28Seine-Maritime%29_-_Mus%C3%A9e_des_Beaux-Arts_-_%22Rue_Saint-Denis%2C_F%C3%AAte_du_30_juin_1878%22_%28Claude_Monet%2C_1840-1926%29_%2832758484702%29.jpg) | 同一天的另一条街，旗子更密。 |


## 4. 备选

录音可用，但曲子或演奏有保留。

### 欢乐岛 · L'isle joyeuse

1904。夏天、河上、岛：船上的午宴（沙图岛）、青蛙塘、阿涅尔、大碗岛、帆船赛。唯一能用的录音底噪明显、速度偏慢（7:38），是这批里最弱的，最好在 Musopen 找一版替换。 Musopen 上还有 Pandora Selfridge 的公有领域版本，这次先没下。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| L'isle joyeuse | Jim Millar, piano | CC BY 3.0 — credit required | 7:38 | [来源](https://imslp.org/wiki/Special:ImagefromIndex/157207) · 本地 `candidates/isle-millar-ccby3.mp3` · Noticeable hiss (about −61 dBFS at 4–8 kHz in quiet passages after normalizing), 7 clipped runs, and slow at 7:38 (usual 5½–6½ min). Weakest of the set. Wayback copy of the IMSLP file (2019-06-07). |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 船上的午宴 Luncheon of the Boating Party | 1880–81 | 华盛顿菲利普斯收藏馆 The Phillips Collection | [Commons](https://commons.wikimedia.org/wiki/File:Pierre-Auguste_Renoir_-_Luncheon_of_the_Boating_Party_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Pierre-Auguste_Renoir_-_Luncheon_of_the_Boating_Party_-_Google_Art_Project.jpg) | 沙图岛上 Fournaise 餐馆的阳台，午餐刚结束，条纹遮阳篷下一桌朋友，身后是塞纳河。标题“欢乐岛”和这座岛正好对上。 |
| 克劳德·莫奈 Claude Monet | 青蛙塘 La Grenouillère | 1869 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:La_Grenouill%C3%A8re_MET_DT833.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/La_Grenouill%C3%A8re_MET_DT833.jpg) | 克鲁瓦西的水上咖啡馆“青蛙塘”，中间的小圆岛叫“花盆”，人们在跳板上下水。 |
| 乔治·修拉 Georges Seurat | 阿涅尔的浴者 Bathers at Asnières | 1884 | 伦敦国家美术馆 National Gallery, London | [Commons](https://commons.wikimedia.org/wiki/File:Baigneurs_a_Asnieres.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Baigneurs_a_Asnieres.jpg) | 塞纳河岸，工人们晒太阳、泡脚，远处是克利希的工厂烟囱。点彩前夜。 |
| 乔治·修拉 Georges Seurat | 大碗岛的星期天下午 A Sunday on La Grande Jatte | 1884–86 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Georges_Seurat_-_Un_dimanche_apr%C3%A8s-midi_%C3%A0_l%27%C3%AEle_de_la_Grande_Jatte.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/A_Sunday_on_La_Grande_Jatte%2C_Georges_Seurat%2C_1884.jpg) | 也是一座岛：周日下午，阳伞、小狗、猴子、帆船。写实版可以拍得很“照片”，再溶成点彩。 |
| 克劳德·莫奈 Claude Monet | 阿让特伊的帆船赛 Regattas at Argenteuil | 1872 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Regattas_at_Argenteuil_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Regattas_at_Argenteuil_-_Google_Art_Project.jpg) | 阿让特伊河湾，白帆和岸边房屋在水里拉成一道道倒影。 |


### 神圣舞曲 · Danse sacrée

《神圣与世俗舞曲》第 1 首，1904。古调式的竖琴，配德加的排练厅和舞台。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Danse sacrée (Danses pour harpe et orchestre, 1) | United States Marine Chamber Orchestra, cond. Jason K. Fettig, harp Karen Grimsey (live, 14 Aug 2010) | Public domain (US government work) | 4:50 | [来源](https://commons.wikimedia.org/wiki/File:Danse_Sacr%C3%A9e.ogg) · 本地 `candidates/danse-sacree-usmc-pd.ogg` · Live concert; starts and ends clean. In the score it runs straight into Danse profane — the two can be joined. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 埃德加·德加 Edgar Degas | 舞蹈课 The Ballet Class | 1871–74 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_The_Ballet_Class_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_The_Ballet_Class_-_Google_Art_Project.jpg) | 巴黎歌剧院的排练厅，老教师 Jules Perrot 拄着长杖，女孩们在等轮到自己。 |
| 埃德加·德加 Edgar Degas | 明星（舞台上的舞者） L'Étoile | 约 1876 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_Ballet_%28L%27%C3%89toile%29.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_Ballet_%28L%27%C3%89toile%29.jpg) | 从包厢俯视，台上独舞的芭蕾女星正做一个 arabesque，布景后露出半个黑衣男人。 |
| 埃德加·德加 Edgar Degas | 舞台上的芭蕾排练 Ballet Rehearsal on Stage | 1874 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_Ballet_Rehearsal_on_Stage_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_Ballet_Rehearsal_on_Stage_-_Google_Art_Project.jpg) | 舞台排练，煤气脚灯从下往上照，几乎是单色。 |


### 博士进阶 · Doctor Gradus ad Parnassum

《儿童乐园》第 1 首，1908。《儿童乐园》写给练琴的小孩，配《钢琴前的少女》，两分钟的小彩蛋。Ligoratti 的《小黑人步态舞》（Golliwogg's Cakewalk）也可以放这里，更活泼。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Doctor Gradus ad Parnassum (Children's Corner, 1) | eldüendesüarez, piano | CC BY 4.0 — credit required | 2:06 | [来源](https://commons.wikimedia.org/wiki/File:Debussy_-_Doctor_Gradys_ad_Parnassum_(Children%27s_Corner)_(Piano_Performance_by_eld%C3%BCendes%C3%BCarez).wav) · 本地 `candidates/doctor-gradus-elduendesuarez-ccby4.wav` · Home recording, peaks at −0.1 dBFS. |
| Golliwogg's Cakewalk (Children's Corner, 6) | Stefano Ligoratti, piano (live) | CC BY 4.0 — credit required | 2:59 | [来源](https://imslp.org/wiki/Special:ImagefromIndex/319772) · 本地 `candidates/golliwogg-ligoratti-ccby4.mp3` · Live. Wayback copy of the IMSLP file (2021-05-13). |
| Danse (Tarantelle styrienne) | eldüendesüarez, piano | CC BY 4.0 — credit required | 5:20 | [来源](https://commons.wikimedia.org/wiki/File:Debussy_-_Danse_(Piano_Performance_by_eld%C3%BCendes%C3%BCarez).wav) · 本地 `candidates/danse-tarantelle-elduendesuarez-ccby4.wav` |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 钢琴前的少女 Young Girls at the Piano | 1892 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Auguste_Renoir_-_Young_Girls_at_the_Piano_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Auguste_Renoir_-_Young_Girls_at_the_Piano_-_Google_Art_Project.jpg) | 家里的客厅，两个女孩一起看一页乐谱。配《博士进阶》（Children's Corner 第一首，写给练琴的小孩）。 |


### 大海（管乐团改编） · La mer — De l'aube à midi sur la mer

1905；美国空军乐队的管乐改编。《印象·日出》就是海上的黎明。但这是管乐团改编，不是原来的管弦乐，音色差很多，列为备选。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| La mer — I. De l'aube à midi sur la mer (concert band arrangement by Lawrence Odom) | United States Air Force Band, Concert Band (2000) | Public domain (US government work) | 9:20 | [来源](https://commons.wikimedia.org/wiki/File:La_mer_-_I._De_l%27aube_%C3%A0_midi_sur_la_mer_-_Concert_Band_-_United_States_Air_Force_Band.mp3) · 本地 `candidates/la-mer-1-usaf-band-pd.mp3` · Wind-band transcription, not the orchestral original. Peaks at +0.1 dBFS. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 印象·日出 Impression, Sunrise | 1872 | 巴黎玛摩丹莫奈博物馆 Musée Marmottan Monet | [Commons](https://commons.wikimedia.org/wiki/File:Monet_-_Impression%2C_Sunrise.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Monet_-_Impression%2C_Sunrise.jpg) | 勒阿弗尔港日出，雾里是起重机和桅杆，水上两只小船。“印象派”这个词就从它来。 |
| 克劳德·莫奈 Claude Monet | 特鲁维尔海滩上的卡米耶 Camille on the Beach in Trouville | 1870 | 耶鲁大学美术馆 Yale University Art Gallery | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Camille_on_the_Beach_in_Trouville_-_1998.46.1_-_Yale_University_Art_Gallery.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Camille_on_the_Beach_in_Trouville_-_1998.46.1_-_Yale_University_Art_Gallery.jpg) | 诺曼底海滩，阳伞下的卡米耶，画里据说还粘着真的沙子。 |
| 克劳德·莫奈 Claude Monet | 普尔维尔的悬崖步道 Cliff Walk at Pourville | 1882 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Cliff_Walk_at_Pourville_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Cliff_Walk_at_Pourville_-_Google_Art_Project.jpg) | 悬崖顶的草地，两位撑伞的女子看海，风很大。 |
| 克劳德·莫奈 Claude Monet | 日出（海景） Sunrise (Marine) | 1873 | 洛杉矶盖蒂美术馆 J. Paul Getty Museum（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_%28French_-_Sunrise_%28Marine%29_-_Google_Art_Project_%28cropped%29.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_%28French_-_Sunrise_%28Marine%29_-_Google_Art_Project_%28cropped%29.jpg) | 勒阿弗尔外海的日出，灰蓝的雾里一轮低低的太阳，水上几条船的剪影。 |
| 克劳德·莫奈 Claude Monet | 曼纳波特（埃特勒塔） The Manneporte (Étretat) | 1883 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_La_Manneporte_%28%C3%89tretat%29.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_La_Manneporte_%28%C3%89tretat%29.jpg) | 埃特勒塔的巨大海蚀拱门，从海滩上仰看，海浪拍着拱门脚下的礁石。 |
| 克劳德·莫奈 Claude Monet | 圣阿德雷斯的海滩 The Beach at Sainte-Adresse | 1867 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Beach_at_Sainte-Adresse_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Beach_at_Sainte-Adresse_-_Google_Art_Project.jpg) | 勒阿弗尔旁边的海滩，岸上拉着几条渔船，渔民和游客，海上很多帆，阴天。 |
| 克劳德·莫奈 Claude Monet | 圣阿德雷斯的花园 Garden at Sainte-Adresse | 1867 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Garden_at_Sainte-Adresse_MET_DT48.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Garden_at_Sainte-Adresse_MET_DT48.jpg) | 海边阳台花园，正午强光，两根旗杆上的旗子被风吹开，花坛、坐着的人，海上满是帆船和轮船的烟。 |


### 牧神午后 · Prélude à l'après-midi d'un faune

1894。夏日午后、草地、风和光：撑阳伞的女人、罂粟花田、摇篮、树下读书。这组画原本给《梦》准备，《梦》没有可用录音，正好给《牧神午后》。这是管弦乐原版，哥伦比亚大学乐团的现场录音，9 分钟。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Prélude à l'après-midi d'un faune | Columbia University Orchestra, cond. Jeffrey Milarsky (Fall 2002 concert, live) | Public domain (Musopen) | 9:14 | [来源](https://musopen.org/music/42994-prelude-to-the-afternoon-of-a-faun/) · 本地 `candidates/faune-columbia-univ-orch-pd.mp3` · Musopen download 2026-10-14. The orchestral original (not an arrangement), student orchestra live; 128 kbps MP3 cut at 15 kHz, no clipping, no applause in the tail. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 撑阳伞的女人（莫奈夫人和儿子） Woman with a Parasol – Madame Monet and Her Son | 1875 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son%2C_1875%2C_NGA_61379.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son%2C_1875%2C_NGA_61379.jpg) | 阿让特伊的草坡，仰拍，风吹起面纱和裙摆，云很快。 |
| 克劳德·莫奈 Claude Monet | 罂粟花田 Poppies | 1873 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Poppy_Field_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Poppy_Field_-_Google_Art_Project.jpg) | 阿让特伊的罂粟花坡，母子两人从坡上走下来。 |
| 贝尔特·莫里索 Berthe Morisot | 摇篮 The Cradle | 1872 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Berthe_Morisot_-_The_Cradle_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Berthe_Morisot_-_The_Cradle_-_Google_Art_Project.jpg) | 白纱帐里睡着的婴儿，母亲托着腮看她。 |
| 克劳德·莫奈 Claude Monet | 春天（读书的女子） Springtime | 1872 | 巴尔的摩沃尔特斯美术馆 Walters Art Museum（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Springtime_-_Walters_3711.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Springtime_-_Walters_3711.jpg) | 树下读书的卡米耶，阳光透过叶子落在白裙上。 |


### 塔 · Pagodes

《版画集》第 1 首，1903。日本趣味：穿和服的卡米耶、梵高仿广重。Howard Lam 的录音压缩很重、强弱对比弱，有削波，先听再定。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Pagodes (Estampes, 1) | Howard Lam, piano | Public domain (performer's dedication on Musopen) | 5:45 | [来源](https://musopen.org/music/4488-estampes-l-100/) · 本地 `candidates/pagodes-howard-lam-pd.mp3` · Musopen download 2026-10-14. The MP3 was transcoded from a YouTube audio stream and is heavily compressed (loudness range 6 LU, normal piano recordings here are 13–22) with 293 clipped runs. 5:45 is on the slow side (usual 4½–5½ min). |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 日本女人（穿和服的莫奈夫人） La Japonaise | 1876 | 波士顿美术馆 Museum of Fine Arts, Boston | [Commons](https://commons.wikimedia.org/wiki/File:Monet_Japonaise.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Monet_Japonaise.jpg) | 金发的卡米耶穿着大红和服回头，墙上贴满团扇。 |
| 文森特·梵高 Vincent van Gogh | 开花的梅园（仿广重） Flowering Plum Orchard (after Hiroshige) | 1887 | 阿姆斯特丹梵高博物馆 Van Gogh Museum | [Commons](https://commons.wikimedia.org/wiki/File:Bloeiende_pruimenboomgaard_%28naar_Hiroshige%29_-_s0115V1962_-_Van_Gogh_Museum.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Bloeiende_pruimenboomgaard_%28naar_Hiroshige%29_-_s0115V1962_-_Van_Gogh_Museum.jpg) | 梵高临摹歌川广重的浮世绘，写实版可以直接拍一棵老梅树。 |


### 雨中花园 · Jardins sous la pluie

《版画集》第 3 首，1903。卡耶博特的雨天、雷诺阿的雨伞、梵高的雨。Howard Lam 的录音几乎被压平了（强弱只差约 8 dB），统一音量也救不回来，先听再定。

| 录音 | 演奏 | 许可 | 时长 | 来源 / 本地 |
|---|---|---|---|---|
| Jardins sous la pluie (Estampes, 3) | Howard Lam, piano | Public domain (performer's dedication on Musopen) | 3:25 | [来源](https://musopen.org/music/4488-estampes-l-100/) · 本地 `candidates/jardins-pluie-howard-lam-pd.mp3` · Musopen download 2026-10-14. Transcoded from a YouTube audio stream and squashed almost flat (loudness range 2 LU: loud and quiet passages only about 8 dB apart), 37 clipped runs, cut at 16 kHz. Normalizing cannot restore the dynamics. |

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 古斯塔夫·卡耶博特 Gustave Caillebotte | 巴黎街道，雨天 Paris Street; Rainy Day | 1877 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Gustave_Caillebotte_-_Paris_Street%3B_Rainy_Day_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Gustave_Caillebotte_-_Paris_Street%3B_Rainy_Day_-_Google_Art_Project.jpg) | 都柏林广场的路口，雨天，鹅卵石反光，撑伞的行人迎面走来。这幅本来就很像照片。 |
| 皮埃尔-奥古斯特·雷诺阿 Pierre-Auguste Renoir | 雨伞 The Umbrellas | 约 1881–86 | 伦敦国家美术馆 National Gallery, London | [Commons](https://commons.wikimedia.org/wiki/File:Pierre-Auguste_Renoir%2C_The_Umbrellas%2C_ca._1881-86.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Pierre-Auguste_Renoir%2C_The_Umbrellas%2C_ca._1881-86.jpg) | 巴黎街头一片雨伞，前景提篮子的女子和拿铁环的小女孩。 |
| 文森特·梵高 Vincent van Gogh | 雨 Rain | 1889 | 费城艺术博物馆 Philadelphia Museum of Art | [Commons](https://commons.wikimedia.org/wiki/File:Vincent_Willem_van_Gogh%2C_Dutch_-_Rain_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Vincent_Willem_van_Gogh%2C_Dutch_-_Rain_-_Google_Art_Project.jpg) | 圣雷米疗养院窗外的麦田，雨丝斜斜划过整幅画。后印象派。 |


## 5. 画配好了、还缺录音的曲子

这些配对本来最贴切，录音要在 Musopen 上找（脚本和内置浏览器都被 Cloudflare 人机验证挡住，没有去点验证）。

### 水中倒影 · Reflets dans l'eau

《意象集》第一集，1905。睡莲的本命曲。维基共享资源、IMSLP、Musopen 上都只有 BY-SA / NC / ND 或美国未过保护期的版本。

录音：还没有可用的（PD / CC0 / CC BY）。

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 睡莲 Water Lilies | 1906 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Water_Lilies_-_1933.1157_-_Art_Institute_of_Chicago.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Water_Lilies_-_1933.1157_-_Art_Institute_of_Chicago.jpg) | 吉维尼睡莲池的一小块水面：没有地平线，只有睡莲、天空和柳树的倒影。 |
| 克劳德·莫奈 Claude Monet | 睡莲池上的桥 Bridge over a Pond of Water Lilies | 1899 | 纽约大都会艺术博物馆 The Met（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Bridge_over_a_Pond_of_Water_Lilies_MET_DT1854.jpg) | 吉维尼的日本桥，夏天，绿色主调，桥下满是睡莲。 |
| 克劳德·莫奈 Claude Monet | 日本桥 The Japanese Footbridge | 1899 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_The_Japanese_Footbridge%2C_1899%2C_NGA_74796.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_The_Japanese_Footbridge%2C_1899%2C_NGA_74796.jpg) | 同一座桥，稍微换个角度，紫藤和光更多。 |


### 雾 · Brouillards

《前奏曲》第二集第 1 首，1913。莫奈的伦敦：议会大厦、滑铁卢桥、查令十字桥。Musopen 上只有 Ivan Ilić 的 NC-ND 版本，维基共享资源上是 Free Art License。

录音：还没有可用的（PD / CC0 / CC BY）。

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 伦敦议会大厦，阳光效果 Houses of Parliament, Sunlight Effect | 1903 | 布鲁克林博物馆 Brooklyn Museum | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Houses_of_Parliament%2C_Sunlight_Effect_%28Le_Parlement%2C_effet_de_soleil%29_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Houses_of_Parliament%2C_Sunlight_Effect_%28Le_Parlement%2C_effet_de_soleil%29_-_Google_Art_Project.jpg) | 从圣托马斯医院的阳台看泰晤士河对岸的议会大厦，太阳在雾里。 |
| 克劳德·莫奈 Claude Monet | 伦敦议会大厦 Houses of Parliament, London | 1900–03 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_Houses_of_Parliament%2C_London%2C_1900-1903%2C_1933.1164%2C_Art_Institute_of_Chicago.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_Houses_of_Parliament%2C_London%2C_1900-1903%2C_1933.1164%2C_Art_Institute_of_Chicago.jpg) | 同一机位，雾更浓，只剩剪影。 |
| 克劳德·莫奈 Claude Monet | 滑铁卢桥，阴天 Waterloo Bridge, Gray Weather | 1900 | 芝加哥艺术博物馆 Art Institute of Chicago（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Monet_-_Waterloo_Bridge%2C_Gray_Weather%2C_1900.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Monet_-_Waterloo_Bridge%2C_Gray_Weather%2C_1900.jpg) | 从萨伏伊酒店窗口看滑铁卢桥，马车、烟囱、灰雾。 |
| 克劳德·莫奈 Claude Monet | 查令十字桥 Charing Cross Bridge | 1903 | 圣路易斯艺术博物馆 Saint Louis Art Museum | [Commons](https://commons.wikimedia.org/wiki/File:Monet_-_Charing_Cross_Bridge%2C_1903.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Monet_-_Charing_Cross_Bridge%2C_1903.jpg) | 铁路桥上一列火车冒着烟，雾把一切都变成紫色。 |


### 帆 · Voiles

《前奏曲》第一集第 2 首，1910。阿让特伊的帆船。Musopen 上有 Ilaria Baldaccini 的公有领域版本，这次先没下，名额留到以后。

录音：还没有可用的（PD / CC0 / CC BY）。

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 阿让特伊的桥 The Bridge at Argenteuil | 1874 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_The_Bridge_at_Argenteuil_%281874%29_-_NGA_1983.1.24.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_The_Bridge_at_Argenteuil_%281874%29_-_NGA_1983.1.24.jpg) | 阿让特伊公路桥，桥下停着几艘帆船，水面平静。 |
| 古斯塔夫·卡耶博特 Gustave Caillebotte | 阿让特伊的帆船 Sailing Boats at Argenteuil | 1888 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Gustave_Caillebotte_-_Sailing_Boats_at_Argenteuil_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Gustave_Caillebotte_-_Sailing_Boats_at_Argenteuil_-_Google_Art_Project.jpg) | 泊在岸边的帆船，桅杆竖成一排。 |
| 克劳德·莫奈 Claude Monet | 阿让特伊 Argenteuil | 约 1872 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_Argenteuil%2C_c._1872%2C_NGA_52186.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_Argenteuil%2C_c._1872%2C_NGA_52186.jpg) | 河湾里的帆船和远处的小镇。 |


### 梦 · Rêverie

1890。没有可用录音（Musopen 上只有 NC 版本）。原来配的夏日午后那组画先给了《牧神午后》。

录音：还没有可用的（PD / CC0 / CC BY）。

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 克劳德·莫奈 Claude Monet | 撑阳伞的女人（莫奈夫人和儿子） Woman with a Parasol – Madame Monet and Her Son | 1875 | 华盛顿国家美术馆 National Gallery of Art（开放获取） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet%2C_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son%2C_1875%2C_NGA_61379.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet%2C_Woman_with_a_Parasol_-_Madame_Monet_and_Her_Son%2C_1875%2C_NGA_61379.jpg) | 阿让特伊的草坡，仰拍，风吹起面纱和裙摆，云很快。 |
| 克劳德·莫奈 Claude Monet | 罂粟花田 Poppies | 1873 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Poppy_Field_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Poppy_Field_-_Google_Art_Project.jpg) | 阿让特伊的罂粟花坡，母子两人从坡上走下来。 |
| 贝尔特·莫里索 Berthe Morisot | 摇篮 The Cradle | 1872 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Berthe_Morisot_-_The_Cradle_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Berthe_Morisot_-_The_Cradle_-_Google_Art_Project.jpg) | 白纱帐里睡着的婴儿，母亲托着腮看她。 |
| 克劳德·莫奈 Claude Monet | 春天（读书的女子） Springtime | 1872 | 巴尔的摩沃尔特斯美术馆 Walters Art Museum（CC0） | [Commons](https://commons.wikimedia.org/wiki/File:Claude_Monet_-_Springtime_-_Walters_3711.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Claude_Monet_-_Springtime_-_Walters_3711.jpg) | 树下读书的卡米耶，阳光透过叶子落在白裙上。 |


### 第一阿拉贝斯克（钢琴） · Première Arabesque

1891。钢琴版没有可用录音：Musopen 上唯一的 CC BY 版本是从 YouTube 扒的低音质文件（见“不能用”）。只剩 1920 年竖琴版（见备选）。

录音：还没有可用的（PD / CC0 / CC BY）。

| 画家 | 画 | 年份 | 收藏 | 图 | 写实还原要点 |
|---|---|---|---|---|---|
| 埃德加·德加 Edgar Degas | 舞蹈课 The Ballet Class | 1871–74 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_The_Ballet_Class_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_The_Ballet_Class_-_Google_Art_Project.jpg) | 巴黎歌剧院的排练厅，老教师 Jules Perrot 拄着长杖，女孩们在等轮到自己。 |
| 埃德加·德加 Edgar Degas | 明星（舞台上的舞者） L'Étoile | 约 1876 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_Ballet_%28L%27%C3%89toile%29.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_Ballet_%28L%27%C3%89toile%29.jpg) | 从包厢俯视，台上独舞的芭蕾女星正做一个 arabesque，布景后露出半个黑衣男人。 |
| 埃德加·德加 Edgar Degas | 舞台上的芭蕾排练 Ballet Rehearsal on Stage | 1874 | 巴黎奥赛博物馆 Musée d'Orsay | [Commons](https://commons.wikimedia.org/wiki/File:Edgar_Degas_-_Ballet_Rehearsal_on_Stage_-_Google_Art_Project.jpg) · [原图](https://commons.wikimedia.org/wiki/Special:FilePath/Edgar_Degas_-_Ballet_Rehearsal_on_Stage_-_Google_Art_Project.jpg) | 舞台排练，煤气脚灯从下往上照，几乎是单色。 |


## 6. 查过但不能用的录音

| 录音 | 为什么不用 |
|---|---|
| Marcelle Meyer 1956–57：前奏曲两集、意象集全套（维基共享资源） | 录音在欧盟已过保护期，但在美国要到 2066 年以后；上传者挂的 PD-US-record 标签本身就写明 1947–1956 年的录音保护 110 年。和之前排除卡萨尔斯 1939 一样的情况。 |
| Giorgi Latso《水中倒影》《向拉莫致敬》（维基共享资源 / IMSLP） | CC BY-SA 4.0 / BY-NC-SA。 |
| Jacopo Salvatori 意象集、贝加莫组曲、欢乐岛（IMSLP / archive.org） | BY-NC-SA。 |
| Richter、Firkušný、Novaes、Haas、Freire、Bernstein、Paray 等名家录音（IMSLP） | 标为 Public Domain – Non-PD US，美国未过保护期。 |
| Patrizia Prati 两首阿拉贝斯克、前奏曲若干（维基共享资源） | CC BY-SA 4.0。 |
| eldüendesüarez 两首阿拉贝斯克、《月光》 | CC BY-SA 4.0（他的《博士进阶》和《舞曲》是 CC BY 4.0，可用）。 |
| La Pianista《比缓慢更缓慢》（维基共享资源） | 演奏部分 CC BY-SA 3.0 / GFDL，文件页的“Public domain”只指作品。 |
| Park Sisters《亚麻色头发的少女》（小提琴+钢琴，维基共享资源） | Commons 标 CC BY 4.0，但来源网站写的是 CC BY-SA 4.0，以网站为准。 |
| Reverie.ogg（维基共享资源） | 没有演奏者、没有来源，只挂了作品的 PD 标签，不可信。 |
| Clair de Lune (1905, piano solo).opus（维基共享资源，来自 YouTube） | 演奏者不明，只挂了作品的 PD 标签。 |
| Giorgi Latsabidze 前奏曲第二集 12 首（维基共享资源） | Free Art License，copyleft，相当于 BY-SA。 |
| Sarah Bassingthwaite《Syrinx》长笛 | CC BY-SA 2.0（EFF OAL）。 |
| Eunmi Ko《欢乐岛》《面具》；Nuages (VPO) | CC BY-SA。 |
| 德彪西本人的钢琴卷（IMSLP《儿童乐园》全集） | 1913 年的 Welte 卷，但音频是 2004 年 Dal Segno 公司的录音，录音本身有权利；IMSLP 标 PD 不可靠。 |
| classicals.de（Gregor Quendel）的《梦》《水中倒影》《欢乐岛》《阿拉贝斯克》等 | 标准许可是 CC BY-NC 4.0，商用要另买授权。 |
| Jeremy Denk 前奏曲现场（Free Music Archive，加德纳博物馆） | CC BY-NC-ND 3.0。 |
| Irén Marik《叶间钟声》（Free Music Archive） | CC BY-NC-SA 3.0。 |
| NASA《月光》可视化里的《月光》（维基共享资源标 NASA 公有领域） | 音乐是 Timothy Michael Hammond 演奏、Killer Tracks 发行的商业配乐，只是授权给 NASA 用，不是公有领域。 |
| Iturbi 1946《两首阿拉贝斯克》、Schmitz 约 1940《梦》（archive.org 78 转唱片） | archive.org 标公有领域，但美国 1946 年出版的录音保护到 2046 年，约 1940 年的到 2040 年左右。 |
| 《Les génies du classique》1991 年 CD 合集（archive.org，含《水中倒影》《雨中花园》《塔》） | 1991 年的商业 CD，上传者挂的 PD 标记不成立。 |
| Musopen Kickstarter 合集（archive.org 镜像） | 是公有领域，但里面没有德彪西。 |
| Musopen「Anonymous」钢琴《第一阿拉贝斯克》（CC BY，已下载） | 22 kHz 单声道 64 kbps，文件名带 youtube，是从 YouTube 扒下来再上传的；演奏者不明，音质也不够。 |
| Musopen「European Archive」前奏曲第一集全套（标公有领域） | 查不到演奏者和录音年代，来路不明。 |
| Musopen 上的《月光》《梦》《水中倒影》《雾》《比缓慢更缓慢》《儿童乐园》（Gerluz、Renzi、Salvatori、Ilić、Riverside Wind Consort 等） | 都是 NC、ND 或 SA。 |
| Ada Sassoli 1920 竖琴版《第一阿拉贝斯克》（LoC，公有领域） | 老唱片底噪太重，2026-10-14 按你的意见删除（文件在废纸篓 debussy-arabesque-harp-20261014）。 |

## 7. 文件在哪

- 原始录音：`lucas-academy-video-data/debussy-impressions/music/candidates/`，来源和许可在 `music/sources.json`。
- 统一音量后的录音：`music/normalized/*.wav`（48 kHz / 24-bit，全部 −18 LUFS、真峰值 ≤ −1 dBTP，和原录音逐采样对齐），由 `scripts/debussy-impressions/normalize.py` 生成，每首的增益和削峰记在 `music/normalized/report.json`。音质测量（频宽、底噪、削波）在 `music/audio_report.jsonl`，由 `audio_report.py` 生成。
- 画：`paintings.json`（Commons 文件名、收藏、写实还原要点），960 px 预览图在 `preview/img/`。原图按表里的“原图”链接下载（Special:FilePath 直接给原件）。
- 预览页：`preview/index.html`（试听用的 96 kbps mp3 在 `preview/audio/`）。
