/* =========================================================
   Caja / Contenedor Individual para Microtubo de 0.5 mL
   (Base + Tapa incluida)
   ========================================================= */

$fn = 60; // Suavizado de círculos

// --- Dimensiones del microtubo (con holguras de impresión) ---
tube_body_dia    = 8.4;   // Diámetro superior del cuerpo cilíndrico (mm)
cone_tip_dia     = 4.5;   // Diámetro en la base del cono inferior (mm)
cone_height      = 12.0;  // Altura de la sección cónica (mm)
cylinder_height  = 16.0;  // Altura del cuerpo recto superior (mm)

rim_dia          = 13.5;  // Diámetro exterior del borde/anillo superior (mm)
rim_depth        = 3.5;   // Profundidad para el borde y bisagra de la tapa (mm)

// --- Dimensiones de la caja exterior ---
wall_thickness   = 3.5;   // Grosor de pared
base_size        = 22.0;  // Ancho y largo exterior (mm)
base_height      = 34.0;  // Altura total de la base (mm)
corner_radius    = 3.0;   // Redondeo de las esquinas exteriores (mm)

// --- Ajuste de la tapa ---
lip_height       = 4.0;   // Altura del rebaje donde calza la tapa (mm)
lip_inset        = 1.5;   // Espesor del labio de ajuste (mm)
lid_tolerance    = 0.25;  // Holgura entre base y tapa para un calce suave (mm)
lid_inner_h      = 5.0;   // Altura interna de la tapa para cubrir la cabeza (mm)

// --- Renderizado en el espacio de trabajo ---
// Muestra la base y la tapa una al lado de la otra listas para imprimir:
caja_base();

translate([base_size + 8, 0, 0])
    caja_tapa();


// ==================== MÓDULOS ====================

// 1. BASE DEL CONTENEDOR
module caja_base() {
    difference() {
        // Bloque exterior
        rounded_cube([base_size, base_size, base_height], corner_radius);

        // Rebaje exterior superior (labio de acople para la tapa)
        translate([0, 0, base_height - lip_height])
            difference() {
                translate([-1, -1, 0]) 
                    cube([base_size + 2, base_size + 2, lip_height + 1]);
                
                translate([lip_inset, lip_inset, -1])
                    rounded_cube([base_size - 2*lip_inset, base_size - 2*lip_inset, lip_height + 2], max(1, corner_radius - lip_inset));
            }

        // Cavidad interior del tubo (centrada)
        translate([base_size/2, base_size/2, 0]) {
            // Fondo cónico (inicia a 3mm del suelo para buen grosor de base)
            translate([0, 0, 3.0])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            // Cilindro recto
            translate([0, 0, 3.0 + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            // Alojamiento del labio superior y bisagra
            translate([0, 0, base_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            // Orificio pasante en la base (para drenaje o expulsar con clip/aguja si se traba)
            translate([0, 0, -1])
                cylinder(h = 5, d = 2.5);
        }
    }
}

// 2. TAPA PROTECTORA
module caja_tapa() {
    lid_wall = 2.0;
    lid_total_h = lip_height + lid_inner_h + lid_wall;

    difference() {
        // Exterior idéntico al perfil de la base
        rounded_cube([base_size, base_size, lid_total_h], corner_radius);

        // Hueco interior para encajar sobre el labio de la base
        translate([lip_inset - lid_tolerance, lip_inset - lid_tolerance, lid_wall])
            rounded_cube([
                base_size - 2*(lip_inset - lid_tolerance), 
                base_size - 2*(lip_inset - lid_tolerance), 
                lid_total_h + 1
            ], max(1, corner_radius - lip_inset));
    }
}

// 3. CUBO REDONDEADO AUXILIAR
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