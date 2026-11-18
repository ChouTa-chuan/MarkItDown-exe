# 基本包已知缺口（隨包揭露）

本表與同目錄的 known-gaps.json 由 scripts/known_gaps.py 產生，兩者列出的元件 id 完全相同。
列出的是版本未知、只有建置宣告，或來源未證明已編入 Windows wheel 的元件。列入本表不代表已取得
再散布核准；它只說明這些元件目前知道什麼、不知道什麼。

共 108 項。

| 義務條目 | 元件 id | 名稱 | 來源或所屬 | 為何未知 |
| --- | --- | --- | --- | --- |
| base-cpython | cpython/libffi | libffi | CPython 3.12.10 官方安裝（_ctypes.pyd） | CPython 官方只宣告建置版本 3.4.4，沒有執行期版本觀測 |
| base-qt | pyside/pyside-setup:sources/shiboken6/libshiboken/qt_attribution.json:0 | Python | Qt 6.12.0 上游來源（QtForPython） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | pyside/pyside-setup:sources/shiboken6/shibokenmodule/files.dir/shibokensupport/signature/qt_attribution.json:0 | Python | Qt 6.12.0 上游來源（QtForPython） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt-native/PySide6/opengl32sw.dll | PySide6/opengl32sw.dll | 外部 Mesa 軟體 OpenGL（PySide6 內附） | 來源未提供版本，模組來自外部 Mesa |
| base-qt | qt/qtbase:src/3rdparty/D3D12MemoryAllocator/qt_attribution.json:0 | D3D12 Memory Allocator | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/VulkanMemoryAllocator/qt_attribution.json:0 | Vulkan Memory Allocator | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/android/qt_attribution.json:0 | Native Style for Android | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/blake2/qt_attribution.json:0 | BLAKE2 (reference implementation) | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/double-conversion/qt_attribution.json:0 | Efficient Binary-Decimal and Decimal-Binary Conversion Routines for IEEE Doubles | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/easing/qt_attribution.json:0 | Easing Equations by Robert Penner | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/emoji-segmenter/qt_attribution.json:0 | Emoji Segmenter | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/forkfd/qt_attribution.json:0 | forkfd | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/freetype/qt_attribution.json:0 | Freetype 2 | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/freetype/qt_attribution.json:1 | Freetype 2 - zlib | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/freetype/qt_attribution.json:2 | Freetype 2 - Bitmap Distribution Format (BDF) support | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/freetype/qt_attribution.json:3 | Freetype 2 - Portable Compiled Format (PCF) support | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/gradle/qt_attribution.json:0 | Gradle wrapper | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/harfbuzz-ng/qt_attribution.json:0 | HarfBuzz-NG | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/icc/qt_attribution.json:0 | sRGB color profile icc file | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/libjpeg/qt_attribution.json:0 | LibJPEG-turbo | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/libpng/qt_attribution.json:0 | LibPNG | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/libpsl/qt_attribution.json:0 | The Public Suffix List | Qt 6.12.0 上游來源（qtnetwork） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/libpsl/qt_attribution.json:1 | libpsl - C library to handle the Public Suffix List | Qt 6.12.0 上游來源（qtnetwork） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/md4/qt_attribution.json:0 | MD4 | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/md4c/qt_attribution.json:0 | MD4C | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/md5/qt_attribution.json:0 | MD5 | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/pcre2/qt_attribution.json:0 | PCRE2 | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/pcre2/qt_attribution.json:1 | PCRE2 - Stack-less Just-In-Time Compiler | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/pixman/qt_attribution.json:0 | Pixman | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/rfc6234/qt_attribution.json:0 | Secure Hash Algorithms SHA-384 and SHA-512 | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/sha1/qt_attribution.json:0 | Secure Hash Algorithm SHA-1 | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/sha3/qt_attribution.json:0 | Secure Hash Algorithm SHA-3 - brg_endian | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/sha3/qt_attribution.json:1 | Secure Hash Algorithm SHA-3 - Keccak | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/siphash/qt_attribution.json:0 | SipHash Algorithm | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/sqlite/qt_attribution.json:0 | SQLite | Qt 6.12.0 上游來源（qtsql） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/tinycbor/qt_attribution.json:0 | TinyCBOR | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wasm/qt_attribution.json:0 | DejaVu Fonts | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/appmenu/qt_attribution.json:0 | Wayland KDE DBus Menu Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/color-management/qt_attribution.json:0 | Wayland Color Management Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/fractional-scale/qt_attribution.json:0 | Wayland Fractional Scale Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/fullscreen-shell/qt_attribution.json:0 | Wayland Fullscreen Shell Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/linux-dmabuf/qt_attribution.json:0 | Wayland Linux Dmabuf V1 Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/linux-dmabuf/qt_attribution.json:1 | Wayland Linux Dmabuf Unstable V1 Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/pointer-gestures/qt_attribution.json:0 | Wayland Pointer Gestures Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/pointer-warp/qt_attribution.json:0 | Wayland Pointer Warp Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/presentation-time/qt_attribution.json:0 | Presentation Time Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/scaler/qt_attribution.json:0 | Wayland Scaler Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/session-management/qt_attribution.json:0 | Wayland Session Management Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/tablet/qt_attribution.json:0 | Wayland Tablet Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/text-input/v1/qt_attribution.json:0 | Wayland Text Input Protocol v1 | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/text-input/v2/qt_attribution.json:0 | Wayland Text Input Protocol v2 | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/text-input/v3/qt_attribution.json:0 | Wayland Text Input Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/viewporter/qt_attribution.json:0 | Wayland Viewporter Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/wayland/qt_attribution.json:0 | Wayland Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/wl-eglstream/qt_attribution.json:0 | Wayland EGLStream Controller Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/wlr-data-control/qt_attribution.json:0 | Wlr Data Control Unstable V1 Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/wp-primary-selection/qt_attribution.json:0 | Wayland Primary Selection Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-activation/qt_attribution.json:0 | Wayland xdg-activation Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-decoration/qt_attribution.json:0 | Wayland xdg-decoration Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-dialog/qt_attribution.json:0 | Wayland Dialog Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-foreign/qt_attribution.json:0 | Wayland XDG Foreign Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-output/qt_attribution.json:0 | Wayland XDG Output Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-shell/qt_attribution.json:0 | Wayland XDG Shell Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-system-bell/qt_attribution.json:0 | Wayland XDG System Bell Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wayland/protocols/xdg-toplevel-icon/qt_attribution.json:0 | Wayland xdg-toplevel-icon Protocol | Qt 6.12.0 上游來源（qtwaylandcompositor） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/3rdparty/wintab/qt_attribution.json:0 | Wintab API | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/xcb/qt_attribution.json:0 | XCB-XInput | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/3rdparty/zlib/qt_attribution.json:0 | Data Compression Library (zlib) | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/corelib/global/qt_attribution.json:0 | tl::expected | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/corelib/kernel/qt_attribution.json:0 | QEventDispatcher on macOS | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/corelib/mimetypes/3rdparty/qt_attribution.json:0 | Apache Tika MimeType Definitions | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/corelib/text/qt_attribution.json:0 | Unicode Character Database (UCD) | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/corelib/text/qt_attribution.json:1 | Unicode Common Locale Data Repository (CLDR) | Qt 6.12.0 上游來源（qtcore） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/dbus/qt_attribution.json:0 | libdbus-1 headers | Qt 6.12.0 上游來源（qtdbus） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/gui/opengl/qt_attribution.json:0 | OpenGL Headers | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/gui/opengl/qt_attribution.json:1 | OpenGL ES 2 Headers | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/gui/painting/qt_attribution.json:0 | Anti-aliasing rasterizer from FreeType 2 | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/gui/painting/qt_attribution.json:1 | Smooth Scaling Algorithm | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/gui/painting/qt_attribution.json:2 | X Server helper | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/gui/rhi/qt_attribution.json:0 | Mipmap generator for D3D12 | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/gui/text/qt_attribution.json:0 | Adobe Glyph List For New Fonts | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/gui/util/qt_attribution.json:0 | XSVG | Qt 6.12.0 上游來源（qtsvg） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtbase:src/gui/vulkan/qt_attribution.json:0 | Vulkan API Registry | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtbase:src/plugins/platforms/cocoa/qt_attribution.json:0 | Cocoa Platform Plugin | Qt 6.12.0 上游來源（qtgui） | Qt 上游來源未宣告版本 |
| base-qt | qt/qtimageformats:src/3rdparty/libtiff/qt_attribution.json:0 | TIFF Software Distribution (libtiff) | Qt 6.12.0 上游來源（qtimageformats） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-qt | qt/qtimageformats:src/3rdparty/libwebp/qt_attribution.json:0 | WebP (libwebp) | Qt 6.12.0 上游來源（qtimageformats） | Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel |
| base-wheels-cffi | cffi/libffi | libffi（上游建置慣例併入 _cffi_backend） | wheel cffi 2.1.1 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-cryptography | cryptography/rust-dependencies | Rust 相依套件（推定靜態併入 _rust.pyd） | wheel cryptography 50.0.2 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-lxml | lxml/libexslt | libexslt | wheel lxml 6.1.3 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-lxml | lxml/libiconv | iconv（libiconv） | wheel lxml 6.1.3 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-lxml | lxml/zlib | zlib（lxml 所附） | wheel lxml 6.1.3 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-numpy | numpy/gcc-runtime-libgfortran | GCC runtime library（libgfortran） | wheel numpy 2.5.4 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-numpy | numpy/numpy-bundled-sources | numpy 內附第三方原始碼（highway、x86-simd-sort、pocketfft、libdivide、svml、dragon4、pythoncapi-compat、lapack_lite、random 種子演算法） | wheel numpy 2.5.4 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-onnxruntime | onnxruntime/onnxruntime-third-party-superset | ONNX Runtime 第三方聲明（建置超集） | wheel onnxruntime 1.31.1 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pandas | pandas/pandas-bundled-notices | pandas 內附其他第三方（LICENSES 目錄所列：klib、ultrajson、xsimd、numpy 等） | wheel pandas 3.1.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pillow | pillow/fribidi | FriBidi（雙向文字） | wheel pillow 13.0.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pillow | pillow/libyuv | libyuv（影像縮放） | wheel pillow 13.0.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pillow | pillow/raqm | Raqm（文字排版） | wheel pillow 13.0.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/abseil | Abseil | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/fast-float | fast_float（pdfium 內附） | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/freetype | FreeType | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/icu | ICU | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/libjpeg-turbo | libjpeg-turbo | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/libopenjpeg | OpenJPEG | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/libpng | libpng | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/llvm-libc | LLVM libc | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/simdutf | simdutf | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
| base-wheels-pypdfium2 | pypdfium2/zlib | zlib（pdfium 內附） | wheel pypdfium2 5.14.0 | wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本 |
