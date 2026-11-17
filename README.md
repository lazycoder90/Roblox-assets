# Jellyfish Pet (Blockbench → Roblox)

Ubur-ubur blocky putih-emas dengan halo, dibuat dari gambar referensi.

## File
| File | Fungsi |
|---|---|
| `jellyfish/Jellyfish.bbmodel` | Model Blockbench (204 kubus, tekstur tertanam). Buka & edit di Blockbench. |
| `jellyfish/jellyfish_texture.png` | Tekstur 64×64 (putih, putih-bayangan, emas, emas-terang). |
| `jellyfish/export/JellyfishBody.fbx` | Mesh bagian putih (kubah, tentakel). |
| `jellyfish/export/JellyfishGlow.fbx` | Mesh bagian emas (halo, rib, berlian, bintang, ujung tentakel) → diberi Neon. |
| `jellyfish/preview.png`, `preview_side.png` | Render pratinjau. |
| `roblox/JellyfishPet.server.lua` | Script pet: mengikuti pemain, melayang naik-turun, berputar pelan. |
| `tools/build_jellyfish.py` | Generator model (ubah proporsi di sini lalu jalankan ulang). |
| `tools/export_blender.py` | Render + ekspor FBX lewat Blender headless. |

Outliner Blockbench: `Bell`, `Gold_Trim`, `Halo`, `Tentacles/Tentacle_0..7`, `Oral_Arms/Arm_0..3`, `Sparkles`. Kubus berawalan `G_` = bagian glow.

## Regenerasi
```
python3 tools/build_jellyfish.py
/Applications/Blender.app/Contents/MacOS/Blender -b --python tools/export_blender.py
```
Catatan: edit manual di Blockbench akan tertimpa jika generator dijalankan ulang. Setelah edit manual, ekspor langsung dari Blockbench (File → Export → glTF/OBJ).

## Import ke Roblox Studio
1. Asset Manager / 3D Importer → impor kedua FBX. Pastikan posisi kedua mesh tidak diubah (satu origin).
2. Unggah `jellyfish_texture.png`, isi `TextureID` pada Body dan Glow (atau `TEXTURE_ID` di script).
3. Buat Model `JellyfishPet` di `ServerStorage` berisi MeshPart `Body` dan `Glow`.
4. Taruh `JellyfishPet.server.lua` di `ServerScriptService`, lalu Play.

Skala: 1 blok (16 px) = 3 stud saat impor, tinggi total ≈ 11 stud; script memakai `PET_SCALE = 0.5`.
