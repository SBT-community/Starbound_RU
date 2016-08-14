cd "new_mod";
zip ../Russian.zip -r ".";
cd "..";
./tools/asset_packer new_mod Russian.pak;
