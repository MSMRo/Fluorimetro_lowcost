// --- Diseño de Tuerca Mariposa Compacta (Perfil Bajo) ---
$fn = 120;

// Parámetros fijos solicitados (en mm)
diametro_orificio = 8.2; 
altura_base = 8;       

// Parámetros ajustados para orejas cortas y agrupadas al centro
diametro_base = 14.5;    // Núcleo ajustado para dar soporte mecánico al agujero de 8.2mm
largo_oreja = 10.5;      // Extensión reducida para mantener las orejas cerca del centro
grosor_oreja = 3.0;      // Mayor volumen para un aspecto redondeado y robusto
elevacion_punta = 5.5;   // Altura de las orejas en proporción a la base plana

module oreja_corta() {
    hull() {
        // Unión con el núcleo central
        translate([0, 0, 0]) 
            sphere(r = grosor_oreja);
        
        // Punta de la oreja (muy cercana al centro)
        translate([largo_oreja, 0, elevacion_punta]) 
            sphere(r = grosor_oreja * 0.9);
            
        // Lóbulo inferior redondeado
        translate([largo_oreja * 0.65, 0, 0.8]) 
            sphere(r = grosor_oreja * 1.1);
    }
}

difference() {
    union() {
        // Base / Núcleo central
        cylinder(d = diametro_base, h = altura_base, center = true);
        
        // Oreja derecha pegada a la base
        translate([diametro_base/4.2, 0, -altura_base/4])
            oreja_corta();
            
        // Oreja izquierda pegada a la base
        mirror([1, 0, 0])
            translate([diametro_base/4.2, 0, -altura_base/4])
                oreja_corta();
    }
    
    // Perforación central exacta de 8.2 mm
    cylinder(d = diametro_orificio, h = altura_base + 10, center = true);
}