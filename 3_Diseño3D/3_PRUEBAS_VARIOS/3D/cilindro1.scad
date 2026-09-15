grosor=5;
diametro=50;
diam_eje=8;


difference(){
cylinder(r=diametro/2, h=grosor,$fn=100);
cylinder(r=diam_eje/2,h=3*grosor, $fn=20, center=true);
}