\# Croqui Pro Surveyor v9.3



> \*\*Professional Land Surveying, Croqui Design \& Mapping Tool\*\*

> 

> \*\*أداة احترافية للمساحة وتصميم الكروكيات والخرائط\*\*



\[!\[Version](https://img.shields.io/badge/version-9.3%20Final-blue.svg)](https://github.com/)

\[!\[Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://www.python.org/)

\[!\[License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

\[!\[Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()



\---



\## 📖 Table of Contents | جدول المحتويات



\- \[🇬🇧 English Documentation](#-english-documentation)

&#x20; - \[Overview](#overview)

&#x20; - \[Key Features](#-key-features)

&#x20; - \[System Requirements](#-system-requirements)

&#x20; - \[Installation](#-installation)

&#x20; - \[Project Structure](#-project-structure)

&#x20; - \[How to Use](#-how-to-use--step-by-step)

&#x20; - \[Calculations \& Formulas](#-calculations--formulas)

&#x20; - \[Disclaimer](#-disclaimer)

&#x20; - \[Author](#-author)

\- \[🇸🇦 التوثيق العربي](#-التوثيق-العربي)

&#x20; - \[نظرة عامة](#-نظرة-عامة)

&#x20; - \[المميزات الرئيسية](#-المميزات-الرئيسية)

&#x20; - \[متطلبات النظام](#️-متطلبات-النظام)

&#x20; - \[التثبيت](#-التثبيت)

&#x20; - \[هيكل المشروع](#-هيكل-المشروع)

&#x20; - \[طريقة الاستخدام](#-طريقة-الاستخدام--خطوة-بخطوة)

&#x20; - \[الحسابات والصيغ](#-الحسابات-والصيغ)

&#x20; - \[إخلاء المسؤولية](#️-إخلاء-المسؤولية)

&#x20; - \[المؤلف](#-المؤلف)



\---



\# 🇬🇧 English Documentation



\## 📖 Overview



\*\*Croqui Pro Surveyor\*\* is a professional desktop application built with Python for land surveyors, civil engineers, and mapping professionals. It enables users to create accurate, presentation-ready land survey croquis (site plans) with real-time interactive editing, satellite imagery, OpenStreetMap integration, and multi-format export capabilities.



The application combines \*\*geodetic precision\*\* (WGS84 ellipsoid calculations) with \*\*visual interactivity\*\*, allowing surveyors to:



\- 📥 Import coordinates from CSV files or enter them manually

\- 🎯 Visually adjust property corners by dragging on satellite/OSM maps

\- 🌊 Define sea and road features on any property edge

\- 📊 Generate professional croqui documents with coordinate tables, legends, scale bars, and north arrows

\- 📤 Export to PDF, PNG, and DXF (AutoCAD) formats



\---



\## ✨ Key Features



\### 🎯 Interactive Corner Editor

\- \*\*Drag-and-drop corners\*\* on a live satellite or OpenStreetMap background

\- \*\*Independent edge control\*\* — each edge (North, East, South, West) adjusts a single corner without conflicts

\- \*\*Real-time measurements\*\* — area, perimeter, and all four edge lengths update instantly

\- \*\*Zoom support\*\* (levels 15–19) with automatic tile reloading



\### 🌊 Sea \& 🛣️ Road Annotation

\- Mark a \*\*sea\*\* on any property edge (visualized as a blue polygon)

\- Mark a \*\*public road (RR01)\*\* on any edge (visualized as a gray hatched polygon)

\- \*\*Drag the feature directly on the map\*\* to adjust its distance from the property boundary

\- Offsets are preserved in exports



\### 📐 Precise Geodetic Calculations

\- \*\*Area\*\* via geodesic polygon calculation (WGS84 ellipsoid)

\- \*\*Distances\*\* between corners using Vincenty's inverse formula

\- \*\*UTM coordinates\*\* automatically computed (correct zone and hemisphere)

\- \*\*Perimeter and edge lengths\*\* measured with sub-meter accuracy



\### 🗺️ Dual Map Layers

\- \*\*Large map\*\* = OpenStreetMap (street view)

\- \*\*Mini map\*\* = Satellite imagery (location context)

\- Both cached locally at `D:\\croqui\_cache\\` (Windows) or `\~/croqui\_cache/` (Unix)



\### 📊 Professional Croqui Output

\- \*\*Site data table\*\* (type, area, length, width, shape, facings)

\- \*\*Coordinates table\*\* (UTM Easting/Northing for all 4 corners)

\- \*\*Legend\*\* of all symbols used

\- \*\*Scale bar\*\* with automatic range detection

\- \*\*North arrow\*\* in traditional cartographic style

\- \*\*Engineer signature block\*\* with license and date

\- \*\*Custom office logo\*\* support



\### 💾 Export Formats



| Format | Use Case |

|--------|----------|

| \*\*PDF\*\* | Print-ready A3 landscape (300 DPI) |

| \*\*PNG\*\* | High-resolution raster image |

| \*\*DXF\*\* | AutoCAD-compatible drawing with layers |

| \*\*CSV\*\* | Coordinate interchange |

| \*\*JSON\*\* | Full project save/load |



\### 🎨 Customization

\- Arabic font selection (Tahoma, Segoe UI, Cairo, Amiri, Noto Naskh, etc.)

\- Table header and cell color customization

\- Custom office logo upload

\- Editable project metadata (engineer, license, specialty)



\### 💾 Smart Cache System

\- Persistent tile cache on `D:` drive (Windows) or home directory

\- Automatic size monitoring (max 500 MB)

\- One-click cache clearing

\- Offline map access after first download



\---



\## 🖥️ System Requirements



| Component | Requirement |

|-----------|-------------|

| \*\*OS\*\* | Windows 10/11, Linux, macOS |

| \*\*Python\*\* | 3.8 or higher |

| \*\*RAM\*\* | 4 GB minimum (8 GB recommended) |

| \*\*Disk\*\* | 600 MB for cache + application |

| \*\*Display\*\* | 1280×800 minimum (1920×1080 recommended) |

| \*\*Internet\*\* | Required for first-time map tile download |



\---



\## 🚀 Installation



\### Step 1: Install Python



Download and install Python 3.8+ from \[python.org](https://www.python.org/downloads/).



> ⚠️ \*\*Important:\*\* Check \*\*"Add Python to PATH"\*\* during installation.



\### Step 2: Install Required Libraries



Open a terminal (CMD/PowerShell on Windows, Terminal on Linux/macOS) and run:



```bash

pip install requests pillow matplotlib pyproj ezdxf

```



Or install from requirements file:



```bash

pip install -r requirements.txt

```



\### Step 3: Download the Application



Place `3krok.py` in any folder of your choice.



\### Step 4: Run the Application



```bash

python 3krok.py

```



\---



\## 📁 Project Structure



```

Croqui-Pro-Surveyor/

│

├── 3krok.py                 # Main application (single file)

├── README.md                # English documentation

├── README\_AR.md             # Arabic documentation

├── requirements.txt         # Python dependencies

├── LICENSE                  # License file

└── screenshots/             # Application screenshots

&#x20;   ├── startup.png

&#x20;   ├── editor.png

&#x20;   ├── croqui.png

&#x20;   └── export.png

```



\### 📦 requirements.txt



```

requests>=2.28.0

pillow>=9.0.0

matplotlib>=3.5.0

pyproj>=3.3.0

ezdxf>=0.17.0

```



\---



\## 🎬 How to Use — Step by Step



\### Step 1: Launch \& Choose Start Mode



When you run the application, a \*\*Startup Dialog\*\* appears with two options:



\#### Option A — 📥 Import from File



1\. Click \*\*"📂 Choose CSV File"\*\*

2\. Select a CSV/TXT file with 4 corners

3\. The application auto-detects corner names and coordinate order



\*\*CSV Format:\*\*



```csv

name,latitude,longitude

NE,12.5929379,53.83599347

NW,12.5929379,53.83323253

SW,12.59022609,53.83323255

SE,12.59022609,53.83593335

```



\#### Option B — ✏️ Manual Entry



1\. Click \*\*"✏️ Start with Default Coordinates"\*\*

2\. Default coordinates are loaded (can be edited later)

3\. Click the interactive editor to adjust corners visually



\---



\### Step 2: Interactive Corner Editor



The editor opens with:



\- \*\*Left side:\*\* Satellite/OSM map with 4 draggable corner markers

\- \*\*Right side:\*\* Real-time measurements panel



\#### 🎯 Dragging Corners



\- \*\*Click and drag\*\* any of the 4 markers (NE, NW, SW, SE)

\- Area and edge lengths update \*\*in real time\*\*

\- Markers are color-coded:

&#x20; - 🔴 Red = NE (North-East)

&#x20; - 🟢 Green = NW (North-West)

&#x20; - 🔵 Blue = SW (South-West)

&#x20; - 🟠 Orange = SE (South-East)



\#### 📏 Editing Edge Lengths



Each edge has an \*\*independent input field\*\*:



| Edge | Controls | Anchor |

|------|----------|--------|

| \*\*Top (North)\*\* | P1 ↔ P2 | P1 fixed, P2 moves |

| \*\*Right (East)\*\* | P1 ↔ P4 | P1 fixed, P4 moves |

| \*\*Bottom (South)\*\* | P4 ↔ P3 | P4 fixed, P3 moves |

| \*\*Left (West)\*\* | P2 ↔ P3 | P2 fixed, P3 moves |



> ✅ \*\*No conflicts:\*\* Each edge moves a different corner, so you can adjust all four edges independently.



\#### 🌊 Adding Sea



1\. Check \*\*"🌊 Sea Present"\*\*

2\. Select the edge it faces (North/East/South/West)

3\. \*\*Drag the blue polygon\*\* on the map to change its distance from the property

4\. Offset is preserved in the croqui export



\#### 🛣️ Adding Road



1\. Check \*\*"🛣️ Public Road Present"\*\*

2\. Select the edge it runs along

3\. \*\*Drag the gray polygon\*\* to adjust its distance

4\. Road is labeled "RR01" in the output



\#### 🗺️ Map Controls



\- \*\*Toggle button:\*\* Switch between Satellite 🛰️ and OSM 🗺️

\- \*\*Mouse scroll:\*\* Zoom in/out (levels 15–19)

\- \*\*Reset button:\*\* Restore default coordinates



\#### ✅ Confirming



Click \*\*"✅ Confirm Corners"\*\* to return to the main window.



\---



\### Step 3: Main Application Window



The main window contains:



\*\*Top toolbar:\*\*



\- 🔄 \*\*Refresh Preview\*\* — regenerate the croqui with current data

\- 🎯 \*\*Re-select Corners\*\* — reopen the interactive editor

\- 🖼️ \*\*Export PNG\*\* — save as high-res image

\- 📄 \*\*Export PDF\*\* — save as print-ready PDF

\- 📐 \*\*Export DXF\*\* — save as AutoCAD drawing



\*\*Left panel:\*\*



\- 🎯 Interactive Editor button

\- 💾 Cache management

\- 🎨 Font \& colors

\- 🖼️ Logo upload

\- 📂 CSV import/export

\- 📍 Map center info

\- 📐 Corner coordinates

\- 📋 Project metadata

\- 🧭 Facings (optional)



\*\*Right panel:\*\*



\- Live preview of the croqui



\---



\### Step 4: Generate \& Export



1\. Click \*\*"🔄 Refresh Preview"\*\*

2\. Wait for map tiles to download (progress bar shown)

3\. The croqui appears in the right panel

4\. Choose export format:

&#x20;  - \*\*PNG\*\* — for presentations

&#x20;  - \*\*PDF\*\* — for printing (A3 landscape)

&#x20;  - \*\*DXF\*\* — for CAD editing



\---



\## 📊 Calculations \& Formulas



| Quantity | Method |

|----------|--------|

| \*\*Area\*\* | Geodesic polygon area on WGS84 ellipsoid |

| \*\*Perimeter\*\* | Sum of geodesic distances between consecutive corners |

| \*\*Edge lengths\*\* | Vincenty's inverse formula (WGS84) |

| \*\*UTM zone\*\* | `zone = floor((lon + 180) / 6) + 1` |

| \*\*UTM EPSG\*\* | `32600 + zone` (N hemisphere) / `32700 + zone` (S) |

| \*\*Movement along line\*\* | Forward geodesic from anchor with given distance |



\---



\## ⚠️ Disclaimer



This software is provided as a \*\*surveying and mapping assistance tool\*\*. Verify all measurements, coordinates, and results against appropriate professional surveying methods before using them for legal or official purposes.



The author assumes \*\*no liability\*\* for decisions made based on the output of this application.



\---



\## 👨‍💻 Author



\*\*Ameer Baathar\*\* (أمير بعثر)



\*\*Croqui Pro Surveyor\*\* — Version 9.3 Final



\---



\# 🇸🇦 التوثيق العربي



\## 📖 نظرة عامة



\*\*كروكي برو سيرفيور\*\* هو تطبيق مكتبي احترافي مبني بلغة Python، موجّه للمساحين والمهندسين المدنيين ومتخصصي الخرائط. يتيح للمستخدمين إنشاء كروكيات مساحية دقيقة وجاهزة للعرض، مع تحرير تفاعلي فوري، وصور أقمار صناعية، وتكامل مع OpenStreetMap، وإمكانية التصدير بصيغ متعددة.



يجمع البرنامج بين \*\*الدقة الجيوديسية\*\* (حسابات على مجسم WGS84) و\*\*التفاعل البصري\*\*، مما يتيح للمساح:



\- 📥 استيراد الإحداثيات من ملفات CSV أو إدخالها يدوياً

\- 🎯 ضبط أركان الأرض بصرياً بالسحب على الخريطة

\- 🌊 تحديد البحر والطريق العام على أي ضلع

\- 📊 إنشاء كروكي احترافي مع جداول الإحداثيات ومفتاح الرموز ومقياس الرسم وسهم الشمال

\- 📤 التصدير إلى PDF و PNG و DXF (أوتوكاد)



\---



\## ✨ المميزات الرئيسية



\### 🎯 المحرر التفاعلي للأركان



\- \*\*سحب وإفلات الأركان\*\* على خلفية قمر صناعي أو خريطة OpenStreetMap

\- \*\*كل ضلع مستقل تماماً\*\* — كل ضلع (شمالي، شرقي، جنوبي، غربي) يتحكم بنقطة واحدة فقط دون تعارض

\- \*\*قياسات لحظية\*\* — المساحة والمحيط وأطوال الأضلاع تتحدث فوراً

\- \*\*دعم الزوم\*\* (مستويات 15–19) مع إعادة تحميل التايلات تلقائياً



\### 🌊 و 🛣️ تحديد البحر والطريق



\- تحديد \*\*البحر\*\* على أي ضلع (يظهر كمضلع أزرق)

\- تحديد \*\*الطريق العام (RR01)\*\* على أي ضلع (يظهر كمضلع رمادي مخطط)

\- \*\*سحب العنصر مباشرة على الخريطة\*\* لتعديل بعده عن حد الأرض

\- الإزاحة محفوظة في التصدير



\### 📐 حسابات جيوديسية دقيقة



\- \*\*المساحة\*\* بحساب المضلع الجيوديسي على مجسم WGS84

\- \*\*المسافات\*\* بين الأركان باستخدام صيغة Vincenty العكسية

\- \*\*إحداثيات UTM\*\* تُحسب تلقائياً (المنطقة ونصف الكرة الصحيحان)

\- \*\*المحيط وأطوال الأضلاع\*\* بدقة أقل من المتر



\### 🗺️ طبقتان للخريطة



\- \*\*الخريطة الكبيرة\*\* = OpenStreetMap (عرض الشوارع)

\- \*\*الخريطة المصغرة\*\* = صورة قمر صناعي (سياق الموقع)

\- كلاهما مُخزّن محلياً في `D:\\croqui\_cache\\` (ويندوز) أو `\~/croqui\_cache/` (يونكس)



\### 📊 مخرجات كروكي احترافية



\- \*\*جدول بيانات الأرض\*\* (النوع، المساحة، الطول، العرض، الشكل، الواجهات)

\- \*\*جدول الإحداثيات\*\* (Easting/Northing بصيغة UTM للأركان الأربعة)

\- \*\*مفتاح الرموز\*\* لكل الرموز المستخدمة

\- \*\*مقياس الرسم\*\* مع اكتشاف تلقائي للمدى

\- \*\*سهم الشمال\*\* بالطراز الكارتوغرافي التقليدي

\- \*\*خانة توقيع المهندس\*\* مع الترخيص والتاريخ

\- \*\*دعم شعار المكتب\*\* المخصص



\### 💾 صيغ التصدير



| الصيغة | الاستخدام |

|--------|-----------|

| \*\*PDF\*\* | جاهز للطباعة A3 أفقي (300 DPI) |

| \*\*PNG\*\* | صورة عالية الدقة |

| \*\*DXF\*\* | رسم متوافق مع أوتوكاد مع طبقات |

| \*\*CSV\*\* | تبادل الإحداثيات |

| \*\*JSON\*\* | حفظ/تحميل المشروع كاملاً |



\### 🎨 التخصيص



\- اختيار الخط العربي (Tahoma، Segoe UI، Cairo، Amiri، Noto Naskh، وغيرها)

\- تخصيص ألوان رأس الجدول والخلايا

\- رفع شعار المكتب

\- تعديل بيانات المشروع (المهندس، الترخيص، التخصص)



\### 💾 نظام الكاش الذكي



\- كاش دائم للتايلات على قرص `D:` (ويندوز) أو المجلد الرئيسي

\- مراقبة تلقائية للحجم (بحد أقصى 500 ميجابايت)

\- حذف الكاش بضغطة واحدة

\- الوصول للخريطة دون إنترنت بعد التحميل الأول



\---



\## 🖥️ متطلبات النظام



| العنصر | المتطلب |

|--------|---------|

| \*\*نظام التشغيل\*\* | Windows 10/11، Linux، macOS |

| \*\*Python\*\* | 3.8 أو أحدث |

| \*\*الذاكرة\*\* | 4 جيجابايت كحد أدنى (يُفضّل 8) |

| \*\*القرص\*\* | 600 ميجابايت للكاش + التطبيق |

| \*\*الشاشة\*\* | 1280×800 كحد أدنى (يُفضّل 1920×1080) |

| \*\*الإنترنت\*\* | مطلوب للتحميل الأول لخريطة التايلات |



\---



\## 🚀 التثبيت



\### الخطوة 1: تثبيت Python



حمّل وثبّت Python 3.8+ من \[python.org](https://www.python.org/downloads/).



> ⚠️ \*\*مهم:\*\* ضع علامة على \*\*"Add Python to PATH"\*\* أثناء التثبيت.



\### الخطوة 2: تثبيت المكتبات المطلوبة



افتح نافذة أوامر (CMD/PowerShell على ويندوز، Terminal على Linux/macOS) ونفّذ:



```bash

pip install requests pillow matplotlib pyproj ezdxf

```



أو من ملف requirements:



```bash

pip install -r requirements.txt

```



\### الخطوة 3: تنزيل التطبيق



ضع ملف `3krok.py` في أي مجلد تختاره.



\### الخطوة 4: تشغيل التطبيق



```bash

python 3krok.py

```



\---



\## 📁 هيكل المشروع



```

Croqui-Pro-Surveyor/

│

├── 3krok.py                 # التطبيق الرئيسي (ملف واحد)

├── README.md                # التوثيق الإنجليزي

├── README\_AR.md             # التوثيق العربي

├── requirements.txt         # متطلبات Python

├── LICENSE                  # ملف الترخيص

└── screenshots/             # لقطات شاشة للتطبيق

&#x20;   ├── startup.png

&#x20;   ├── editor.png

&#x20;   ├── croqui.png

&#x20;   └── export.png

```



\### 📦 ملف requirements.txt



```

requests>=2.28.0

pillow>=9.0.0

matplotlib>=3.5.0

pyproj>=3.3.0

ezdxf>=0.17.0

```



\---



\## 🎬 طريقة الاستخدام — خطوة بخطوة



\### الخطوة 1: التشغيل واختيار طريقة البدء



عند تشغيل التطبيق تظهر \*\*نافذة البدء\*\* بخيارين:



\#### الخيار أ — 📥 استيراد من ملف



1\. اضغط \*\*"📂 اختر ملف CSV"\*\*

2\. اختر ملف CSV/TXT يحتوي على 4 أركان

3\. يكتشف التطبيق أسماء الأركان وترتيب الإحداثيات تلقائياً



\*\*صيغة CSV:\*\*



```csv

name,latitude,longitude

NE,12.5929379,53.83599347

NW,12.5929379,53.83323253

SW,12.59022609,53.83323255

SE,12.59022609,53.83593335

```



\#### الخيار ب — ✏️ إدخال يدوي



1\. اضغط \*\*"✏️ بدء بالإحداثيات الافتراضية"\*\*

2\. تُحمّل إحداثيات افتراضية (يمكن تعديلها لاحقاً)

3\. افتح المحرر التفاعلي لضبط الأركان بصرياً



\---



\### الخطوة 2: المحرر التفاعلي للأركان



يفتح المحرر بـ:



\- \*\*الجانب الأيسر:\*\* خريطة قمر صناعي/OSM مع 4 علامات أركان قابلة للسحب

\- \*\*الجانب الأيمن:\*\* لوحة القياسات اللحظية



\#### 🎯 سحب الأركان



\- \*\*اضغط واسحب\*\* أي من العلامات الأربع (NE, NW, SW, SE)

\- المساحة وأطوال الأضلاع تتحدث \*\*لحظياً\*\*

\- العلامات مرمّزة بالألوان:

&#x20; - 🔴 أحمر = شمال شرق (NE)

&#x20; - 🟢 أخضر = شمال غرب (NW)

&#x20; - 🔵 أزرق = جنوب غرب (SW)

&#x20; - 🟠 برتقالي = جنوب شرق (SE)



\#### 📏 تعديل أطوال الأضلاع



كل ضلع له \*\*حقل إدخال مستقل\*\*:



| الضلع | يتحكم بـ | المرتكز |

|-------|----------|---------|

| \*\*الشمالي\*\* | P1 ↔ P2 | P1 ثابت، P2 يتحرك |

| \*\*الشرقي\*\* | P1 ↔ P4 | P1 ثابت، P4 يتحرك |

| \*\*الجنوبي\*\* | P4 ↔ P3 | P4 ثابت، P3 يتحرك |

| \*\*الغربي\*\* | P2 ↔ P3 | P2 ثابت، P3 يتحرك |



> ✅ \*\*لا تعارض:\*\* كل ضلع يحرّك نقطة مختلفة، فيمكنك ضبط الأضلاع الأربعة باستقلالية تامة.



\#### 🌊 إضافة البحر



1\. ضع علامة على \*\*"🌊 يوجد بحر"\*\*

2\. اختر الضلع المواجه له (شمالي/شرقي/جنوبي/غربي)

3\. \*\*اسحب المضلع الأزرق\*\* على الخريطة لتغيير بعده عن حد الأرض

4\. الإزاحة محفوظة في تصدير الكروكي



\#### 🛣️ إضافة الطريق



1\. ضع علامة على \*\*"🛣️ يوجد طريق عام"\*\*

2\. اختر الضلع الذي يمر بمحاذاته

3\. \*\*اسحب المضلع الرمادي\*\* لتعديل بعده

4\. الطريق يُسمّى "RR01" في المخرجات



\#### 🗺️ التحكم بالخريطة



\- \*\*زر التبديل:\*\* بين القمر الصناعي 🛰️ و OSM 🗺️

\- \*\*عجلة الماوس:\*\* تكبير/تصغير (مستويات 15–19)

\- \*\*زر إعادة التعيين:\*\* استعادة الإحداثيات الافتراضية



\#### ✅ التأكيد



اضغط \*\*"✅ تأكيد الأركان"\*\* للعودة للنافذة الرئيسية.



\---



\### الخطوة 3: النافذة الرئيسية



تحتوي النافذة على:



\*\*شريط الأدوات العلوي:\*\*



\- 🔄 \*\*تحديث المعاينة\*\* — إعادة توليد الكروكي بالبيانات الحالية

\- 🎯 \*\*إعادة تحديد الأركان\*\* — فتح المحرر التفاعلي مجدداً

\- 🖼️ \*\*تصدير PNG\*\* — حفظ كصورة عالية الدقة

\- 📄 \*\*تصدير PDF\*\* — حفظ كملف PDF جاهز للطباعة

\- 📐 \*\*تصدير DXF\*\* — حفظ كرسم أوتوكاد



\*\*اللوحة اليسرى:\*\*



\- 🎯 زر المحرر التفاعلي

\- 💾 إدارة الكاش

\- 🎨 الخط والألوان

\- 🖼️ رفع الشعار

\- 📂 استيراد/تصدير CSV

\- 📍 معلومات مركز الخريطة

\- 📐 إحداثيات الأركان

\- 📋 بيانات المشروع

\- 🧭 الواجهات (اختياري)



\*\*اللوحة اليمنى:\*\*



\- معاينة حية للكروكي



\---



\### الخطوة 4: التوليد والتصدير



1\. اضغط \*\*"🔄 تحديث المعاينة"\*\*

2\. انتظر تحميل تايلات الخريطة (يظهر شريط التقدم)

3\. يظهر الكروكي في اللوحة اليمنى

4\. اختر صيغة التصدير:

&#x20;  - \*\*PNG\*\* — للعروض التقديمية

&#x20;  - \*\*PDF\*\* — للطباعة (A3 أفقي)

&#x20;  - \*\*DXF\*\* — للتعديل في CAD



\---



\## 📊 الحسابات والصيغ



| الكمية | الطريقة |

|--------|---------|

| \*\*المساحة\*\* | مساحة المضلع الجيوديسي على مجسم WGS84 |

| \*\*المحيط\*\* | مجموع المسافات الجيوديسية بين الأركان المتتالية |

| \*\*أطوال الأضلاع\*\* | صيغة Vincenty العكسية (WGS84) |

| \*\*منطقة UTM\*\* | `zone = floor((lon + 180) / 6) + 1` |

| \*\*EPSG لـ UTM\*\* | `32600 + zone` (نصف شمالي) / `32700 + zone` (جنوبي) |

| \*\*الحركة على خط\*\* | جيوديسي أمامي من المرتكز بمسافة معطاة |



\---



\## ⚠️ إخلاء المسؤولية



يُقدَّم هذا البرنامج كـ\*\*أداة مساعدة في أعمال المساحة ورسم المخططات\*\*. يجب التحقق من جميع القياسات والإحداثيات والنتائج باستخدام الطرق المساحية المهنية المناسبة قبل الاعتماد عليها في المعاملات القانونية أو الرسمية.



لا يتحمل المؤلف \*\*أي مسؤولية\*\* عن قرارات تُتخذ بناءً على مخرجات هذا التطبيق.



\---



\## 👨‍💻 المؤلف



\*\*أمير بعثر\*\* (Ameer Baathar)



\*\*كروكي برو سيرفيور\*\* — الإصدار 9.3 النهائي



\---



<div align="center">



\*\*⭐ If you find this project useful, please consider giving it a star! ⭐\*\*



\*\*⭐ إذا وجدت هذا المشروع مفيداً، لا تنسَ منحه نجمة! ⭐\*\*



Made with ❤️ by \*\*Ameer Baathar\*\*



</div>

