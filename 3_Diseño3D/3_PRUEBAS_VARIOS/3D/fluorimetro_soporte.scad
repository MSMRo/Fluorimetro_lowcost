/* =================================================================
   Portamuestras / Cubeta para Fluorímetro (Microtubo 0.5 mL)
   Disposición óptica a 90° (Ejes X e Y) para LED / Sensor de 3 mm
   ================================================================= */

$fn = 60; // Resolución para cilindros y curvas

// --- Dimensiones del Microtubo de 0.5 mL ---
tube_body_dia    = 8.4;   // Diámetro superior del cuerpo (mm)
cone_tip_dia     = 4.5;   // Diámetro en la base del cono (mm)
cone_height      = 12.0;  // Altura del cono inferior (mm)
cylinder_height  = 16.0;  // Altura del cuerpo cilíndrico (mm)
rim_dia          = 13.5;  // Diámetro para el reborde y pestaña (mm)
rim_depth        = 3.5;   // Profundidad del rebaje para el labio superior (mm)

// --- Dimensiones del Bloque Base ---
base_size        = 24.0;  // Ancho y largo del bloque óptico (mm)
base_height      = 34.0;  // Altura del bloque (mm)
corner_radius    = 3.0;   // Esquinas redondeadas (mm)
tube_bottom_z    = 3.0;   // Altura sobre la base donde descansa la punta del tubo (mm)

// --- Parámetros de la Trayectoria Óptica (Fluorometría) ---
// Altura del eje óptico: apuntando a la zona media-baja del líquido en el cono
optical_height_z = 8.5;   // Altura Z del centro de los haces ópticos (mm)

led_dia          = 3.2;   // Diámetro para LED/Fotodiodo de 3 mm (con 0.2 mm de holgura)
led_pocket_depth = 6.0;   // Profundidad donde se inserta el LED desde la cara externa (mm)
pinhole_dia      = 1.8;   // Apertura/colimador interior que da a la muestra (mm)

// --- Renderizado ---
fluorimetro_soporte();

// ==================== MÓDULOS ====================

module fluorimetro_soporte() {
    difference() {
        // 1. Bloque exterior sólido
        rounded_cube([base_size, base_size, base_height], corner_radius);

        // 2. Cavidad interior para el microtubo
        translate([base_size / 2, base_size / 2, 0]) {
            // Fondo cónico (zona de muestra)
            translate([0, 0, tube_bottom_z])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            // Cuerpo cilíndrico superior
            translate([0, 0, tube_bottom_z + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            // Rebaje para la tapa / pestaña del tubo
            translate([0, 0, base_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            // Chaflán de entrada superior
            translate([0, 0, base_height - 1.0])
                cylinder(h = 1.1, d1 = rim_dia, d2 = rim_dia + 2.0);

            // Orificio inferior pasante (para expulsión si se atasca)
            translate([0, 0, -1])
                cylinder(h = tube_bottom_z + 2, d = 2.5);
        }

        // 3. Canal Óptico en Eje X (ej. Fuente de Excitación / LED)
        // Viene desde la cara X=0 hacia el centro
        translate([-1, base_size / 2, optical_height_z])
            rotate([0, 90, 0])
                cylinder(h = base_size / 2 + 2, d = pinhole_dia);

        // Alojamiento exterior para insertar el LED de 3 mm en X=0
        translate([-1, base_size / 2, optical_height_z])
            rotate([0, 90, 0])
                cylinder(h = led_pocket_depth + 1, d = led_dia);

        // 4. Canal Óptico en Eje Y (a 90° - ej. Detección / Fotodiodo / Sensor de Emisión)
        // Viene desde la cara Y=0 hacia el centro
        translate([base_size / 2, -1, optical_height_z])
            rotate([-90, 0, 0])
                cylinder(h = base_size / 2 + 2, d = pinhole_dia);

        // Alojamiento exterior para insertar el sensor o LED de 3 mm en Y=0
        translate([base_size / 2, -1, optical_height_z])
            rotate([-90, 0, 0])
                cylinder(h = led_pocket_depth + 1, d = led_dia);
    }
}

// Función auxiliar para bordes lisos exteriores
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