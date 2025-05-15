#!/bin/bash
cp ../dist/MKStroboscopeDiscGeneratorGUI.bin ~/rpmbuild/SOURCES/strobodisccreator
cp strobodisccreator.spec ~/rpmbuild/SPECS/
cp strobodisccreator.desktop ~/rpmbuild/SOURCES/
cp strobodisccreator.png ~/rpmbuild/SOURCES/
rpmbuild -ba ~/rpmbuild/SPECS/strobodisccreator.spec
echo '================================================================================'
echo 'sign it: rpm --addsign ~/rpmbuild/RPMS/x86_64/strobodisccreator-1.0-1.x86_64.rpm'
echo '================================================================================'
