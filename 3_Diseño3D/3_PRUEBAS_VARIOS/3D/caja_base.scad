/* =========================================================
   Caja / Soporte Individual para Microtubo de 0.5 mL
   (Solo Base)
   ========================================================= */

$fn = 60; // Suavizado de curvas

// --- Dimensiones del microtubo (con holgura para inserción) ---
tube_body_dia    = 8.4;   // Diámetro del cuerpo cilíndrico superior (mm)
cone_tip_dia     = 4.5;   // Diámetro en la base del cono inferior (mm)
cone_height      = 12.0;  // Altura de la sección cónica (mm)
cylinder_height  = 16.0;  // Altura del cuerpo recto superior (mm)

rim_dia          = 13.5;  // Diámetro para el borde superior y la bisagra (mm)
rim_depth        = 3.5;   // Profundidad para alojar el borde a ras (mm)

// --- Dimensiones de la caja exterior ---
base_size        = 22.0;  // Ancho y largo exterior (mm)
base_height      = 34.0;  // Altura total del bloque (mm)
corner_radius    = 3.0;   // Radio de redondeo de las esquinas exteriores (mm)

// --- Renderizado de la base ---
caja_base_solo();

// ==================== MÓDULOS ====================

module caja_base_solo() {
    difference() {
        // Bloque exterior sólido con esquinas redondeadas
        rounded_cube([base_size, base_size, base_height], corner_radius);

        // Cavidad interior para el microtubo (centrada)
        translate([base_size / 2, base_size / 2, 0]) {
            // Fondo cónico (inicia a 3 mm del suelo)
            translate([0, 0, 3.0])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            // Cilindro central
            translate([0, 0, 3.0 + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            // Rebaje para el borde superior y la pestaña
            translate([0, 0, base_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            // Chamfer/chaflán en la entrada para insertar fácilmente
            translate([0, 0, base_height - 1.0])
                cylinder(h = 1.1, d1 = rim_dia, d2 = rim_dia + 2.0);

            // Orificio inferior pasante (desagüe y expulsión si se traba)
            translate([0, 0, -1])
                cylinder(h = 5, d = 2.5);
        }
    }
}

// Función auxiliar para esquinas redondeadas
module rounded_cube(size, r) {
    x = size[0];
    y = size[1];
    z = size[2];
    hull() {
        translate([r, r, 0])         cylinder(h = z, r = r);
        translate([x - r, r, 0])     cylinder(h = z, r = r);
        translate([r, y - r, 0])     cylinder(h = z, r = r);
        translate([x - r, y - r, 0]) cylinder(h = z, r = r);
    }
}