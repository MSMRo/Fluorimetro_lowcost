/* =================================================================
   Fluorímetro Integrado + Case Arduino Mega 2560 R3 + Tapa Óptica
   - Pared divisoria 100% sólida y rellena (sin ranura pasamuros)
   - Bloques unidos monolíticamente
   - Cavidad para microtubo 0.5 mL 100% pasante y visible
   - Tapa antifugas de luz incluida
   ================================================================= */

$fn = 60;

// =================================================================
// 1. PARÁMETROS DEL CASE ARDUINO MEGA 2560 R3
// =================================================================
mega_pcb_w       = 101.6; 
mega_pcb_d       = 53.34; 
mega_wall        = 3.0;   
mega_floor       = 2.0;   
standoff_h       = 2.5;   

case_outer_h     = 14.0;  
case_inner_h     = case_outer_h - mega_floor; 

standoff_od      = 6.5;   
standoff_id      = 2.8;   // Para tornillo M3

clearance        = 0.8; 
case_inner_x     = mega_pcb_w + clearance * 2;
case_inner_y     = mega_pcb_d + clearance * 2;
case_outer_x     = case_inner_x + mega_wall * 2;
case_outer_y     = case_inner_y + mega_wall * 2;

mega_holes = [
    [14.0, 2.5],
    [15.2, 50.8],
    [90.2, 50.8],
    [96.5, 2.5]
];

usb_w            = 13.5;  
usb_y_pos        = 32.0;  
jack_w           = 11.5;  
jack_y_pos       = 3.0;   

// =================================================================
// 2. PARÁMETROS DEL BLOQUE ÓPTICO Y MICROTUBO 0.5 mL
// =================================================================
block_size       = 38.0;  
block_height     = 38.0;  
corner_radius    = 3.5;

// Dimensiones de la cavidad del tubo de 0.5 mL
bottom_window_dia = 5.5;  // Ventana inferior de visualización (mm)
tube_body_dia     = 8.4;  // Diámetro superior del microtubo (mm)
rim_dia           = 13.5; // Asiento para pestaña/anillo superior (mm)
rim_depth         = 3.5;  // Profundidad del rebaje para la pestaña (mm)

collar_h          = 5.0;  // Altura del cuello exterior para la tapa (mm)
collar_od         = 21.0; // Diámetro exterior del cuello (mm)
collar_id         = 15.0; // Diámetro interior del cuello (mm)

optical_z         = 11.5; // Eje de lectura óptica apuntando a la muestra
pinhole_dia       = 2.0;

tube_pos_x        = block_size / 2; // 19.0 mm
tube_pos_y        = block_size / 2; // 19.0 mm

// Placas AS7341 y Placa LED
pcb_w             = 26.0;
pcb_h             = 18.4;
pocket_depth      = 3.0;
hole_pitch_w      = 20.32;
hole_pitch_h      = 12.70;
mount_screw_dia   = 2.2;
mount_screw_len   = 6.5;

fluor_pos_x       = case_outer_x;
fluor_pos_y       = (case_outer_y - block_size) / 2;

// Parámetros de la tapa
cap_clearance     = 0.25;  
cap_wall          = 2.0;   
cap_top_thick     = 2.5;   
knob_h            = 4.0;   
knob_dia          = 12.0;  

// =================================================================
// RENDERIZADO GENERAL
// =================================================================
fluorimetro_completo();

// Tapa hermética colocada al costado para imprimir
translate([fluor_pos_x + block_size/2, -collar_od - 8, 0])
    tapa_fluorimetro();


// =================================================================
// MÓDULOS
// =================================================================

module fluorimetro_completo() {
    difference() {
        // --- 1. SÓLIDOS (Case + Bloque Óptico + Cuello) ---
        union() {
            case_arduino_mega();

            translate([fluor_pos_x, fluor_pos_y, 0])
                rounded_cube([block_size, block_size, block_height], corner_radius);

            translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, block_height])
                cylinder(h = collar_h, d = collar_od);
        }

        // --- 2. VACIADO MONOLÍTICO DEL MICROTUBO (100% Pasante) ---
        translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, 0])
            cavidad_tubo_unificada();

        // --- 3. MONTAJES ÓPTICOS A 90° ---
        // Montura Cara Y (Sensor AS7341)
        translate([fluor_pos_x, fluor_pos_y, 0])
            cavidad_montura();

        // Montura Cara X (Placa LED a 90°)
        translate([fluor_pos_x + block_size, fluor_pos_y, 0])
            rotate([0, 0, 90])
                cavidad_montura();

        // (Se removió el pasamuros para dejar la pared completamente cerrada)
    }
}

// Cavidad continua pasante de arriba a abajo
module cavidad_tubo_unificada() {
    z_bottom   = -1.0;                         // Atraviesa la base inferior
    z_cone_end = 17.0;                         // Fin de la zona cónica
    z_rim_seat = block_height - rim_depth;     // Asiento de la pestaña (34.5 mm)
    z_top      = block_height + collar_h + 1.0;// Atraviesa la boca del cuello (44 mm)

    rotate_extrude() {
        polygon(points = [
            [0, z_bottom],
            [bottom_window_dia / 2, z_bottom],
            [bottom_window_dia / 2, 5.0],
            [tube_body_dia / 2, z_cone_end],
            [tube_body_dia / 2, z_rim_seat],
            [rim_dia / 2, z_rim_seat],
            [rim_dia / 2, block_height],
            [collar_id / 2, block_height],
            [collar_id / 2, z_top],
            [0, z_top]
        ]);
    }
}

// Cavidad de montaje con rebajes de componentes y agujeros para tornillos
module cavidad_montura() {
    // Canal óptico hacia el centro del microtubo
    translate([tube_pos_x, -1, optical_z])
        rotate([-90, 0, 0])
            cylinder(h = tube_pos_y + 1, d = pinhole_dia);

    // Bolsillo para la placa PCB
    translate([tube_pos_x - pcb_w/2, -0.1, optical_z - pcb_h/2])
        cube([pcb_w, pocket_depth + 0.1, pcb_h]);

    // Rebajes laterales para conectores STEMMA QT
    translate([tube_pos_x - (pcb_w + 3.5)/2, -0.1, optical_z - 3.5])
        cube([pcb_w + 3.5, pocket_depth + 0.1, 7.0]);

    // Rebaje inferior para pines soldados
    translate([tube_pos_x - 9.0, -0.1, optical_z - pcb_h/2 - 2.0])
        cube([18.0, pocket_depth + 0.1, 4.0]);

    // 4 Agujeros de fijación M2 / M2.5
    for (dw = [-hole_pitch_w/2, hole_pitch_w/2]) {
        for (dh = [-hole_pitch_h/2, hole_pitch_h/2]) {
            translate([tube_pos_x + dw, pocket_depth - 0.1, optical_z + dh])
                rotate([-90, 0, 0])
                    cylinder(h = mount_screw_len, d = mount_screw_dia);
        }
    }
}

// Tapa Antifugas de Luz
module tapa_fluorimetro() {
    cap_inner_dia = collar_od + cap_clearance * 2;
    cap_outer_dia = cap_inner_dia + cap_wall * 2;
    cap_inner_h   = collar_h + 1.5; 
    cap_total_h   = cap_inner_h + cap_top_thick;

    union() {
        difference() {
            cylinder(h = cap_total_h, d = cap_outer_dia);

            translate([0, 0, -0.1])
                cylinder(h = cap_inner_h + 0.1, d = cap_inner_dia);

            translate([0, 0, -0.1])
                cylinder(h = 1.0, d1 = cap_inner_dia + 1.2, d2 = cap_inner_dia);
        }

        translate([0, 0, cap_total_h]) {
            cylinder(h = knob_h, d = knob_dia);
            for (a = [0 : 45 : 360]) {
                rotate([0, 0, a])
                    translate([knob_dia/2, 0, knob_h/2])
                        cylinder(h = knob_h, d = 1.5, center = true);
            }
        }
    }
}

// Case Arduino Mega 2560 Calibrado (Pared divisoria continua)
module case_arduino_mega() {
    difference() {
        cube([case_outer_x, case_outer_y, case_outer_h]);

        translate([mega_wall, mega_wall, mega_floor])
            cube([case_inner_x, case_inner_y, case_inner_h + 1.0]);

        // Entrada USB Tipo B
        translate([-1, mega_wall + clearance + usb_y_pos, mega_floor + standoff_h])
            cube([mega_wall + 2, usb_w, case_outer_h]);

        // Entrada Jack DC
        translate([-1, mega_wall + clearance + jack_y_pos, mega_floor + standoff_h])
            cube([mega_wall + 2, jack_w, case_outer_h]);
    }

    for (h = mega_holes) {
        translate([mega_wall + clearance + h[0], mega_wall + clearance + h[1], mega_floor]) {
            difference() {
                cylinder(h = standoff_h, d = standoff_od);
                translate([0, 0, -0.5])
                    cylinder(h = standoff_h + 1.0, d = standoff_id);
            }
        }
    }
}

// Módulo auxiliar de redondeo
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