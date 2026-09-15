/* =================================================================
   Fluorímetro Integrado + Case Arduino Mega 2560 R3 + Tapa Óptica
   - Case con altura ampliada (pared superior cerrada sobre USB y Jack)
   - Microtubo 0.5 mL en el extremo posterior con cuello a prueba de luz
   - Tapa desmontable lista para imprimir
   ================================================================= */

$fn = 50;

// =================================================================
// 1. PARÁMETROS DEL CASE ARDUINO MEGA 2560 R3
// =================================================================
mega_pcb_w       = 101.6; 
mega_pcb_d       = 53.34; 
mega_wall        = 3.0;   
mega_floor       = 2.5;   
standoff_h       = 4.0;   

// --- Altura ampliada para cerrar el marco superior de los puertos ---
case_inner_h     = 14.0;  // Elevado a 22 mm para dejar un puente sólido sobre el USB
standoff_od      = 6.5;   
standoff_id      = 2.8;   // Para tornillo M3

clearance        = 1.0; 
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

// =================================================================
// 2. PARÁMETROS DEL BLOQUE ÓPTICO (FLUORÍMETRO)
// =================================================================
block_size       = 38.0;  
block_height     = 38.0;  
corner_radius    = 3.5;

// Microtubo 0.5 mL
tube_body_dia    = 8.4;
cone_tip_dia     = 4.5;
cone_height      = 12.0;
cylinder_height  = 16.0;
rim_dia          = 13.5;
rim_depth        = 3.5;
tube_bottom_z    = 5.0;

optical_z        = 11.5;
pinhole_dia      = 2.0;

tube_pos_x       = block_size / 2; // 19.0 mm
tube_pos_y       = block_size / 2; // 19.0 mm

// Placas AS7341 y Placa LED
pcb_w            = 26.0;
pcb_h            = 18.4;
pocket_depth     = 3.0;
hole_pitch_w     = 20.32;
hole_pitch_h     = 12.70;
mount_screw_dia  = 2.2;
mount_screw_len  = 6.5;

// Coordenadas de unión con el case
fluor_pos_x      = case_outer_x;
fluor_pos_y      = (case_outer_y - block_size) / 2;

// =================================================================
// 3. PARÁMETROS DE LA TAPA Y CUELLO SUPERIOR
// =================================================================
collar_h         = 5.0;   
collar_od        = 21.0;  
collar_id        = 15.0;  
cap_clearance    = 0.25;  
cap_wall         = 2.0;   
cap_top_thick    = 2.5;   
knob_h           = 4.0;   
knob_dia         = 12.0;  

// =================================================================
// RENDERIZADO GENERAL
// =================================================================
fluorimetro_completo();

// Tapa al costado lista para impresión simultánea
translate([fluor_pos_x + block_size/2, -collar_od - 8, 0])
    tapa_fluorimetro();


// =================================================================
// MÓDULOS
// =================================================================

module fluorimetro_completo() {
    difference() {
        union() {
            // Case para Arduino Mega (con paredes elevadas)
            case_arduino_mega();

            // Bloque óptico del fluorímetro
            translate([fluor_pos_x, fluor_pos_y, 0])
                bloque_fluorimetro();

            // Cuello cilíndrico para la tapa antifugas de luz
            translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, block_height])
                cylinder(h = collar_h, d = collar_od);
        }

        // Cavidad interior del cuello cilíndrico
        translate([fluor_pos_x + tube_pos_x, fluor_pos_y + tube_pos_y, block_height - 0.1])
            cylinder(h = collar_h + 1.0, d = collar_id);

        // Pasamuros de cables entre el Arduino y el bloque óptico
        translate([case_outer_x - mega_wall - 1, fluor_pos_y + 10.0, mega_floor + standoff_h])
            cube([mega_wall + 2, 18.0, 8.0]);
    }
}

// Bloque Óptico del Microtubo
module bloque_fluorimetro() {
    difference() {
        rounded_cube([block_size, block_size, block_height], corner_radius);

        // Cavidad del microtubo de 0.5 mL
        translate([tube_pos_x, tube_pos_y, 0]) {
            translate([0, 0, tube_bottom_z])
                cylinder(h = cone_height, d1 = cone_tip_dia, d2 = tube_body_dia);

            translate([0, 0, tube_bottom_z + cone_height])
                cylinder(h = cylinder_height + 0.1, d = tube_body_dia);

            translate([0, 0, block_height - rim_depth])
                cylinder(h = rim_depth + 1, d = rim_dia);

            translate([0, 0, block_height - 1.2])
                cylinder(h = 1.3, d1 = rim_dia, d2 = rim_dia + 2.5);

            translate([0, 0, -1])
                cylinder(h = tube_bottom_z + 2, d = 2.5);
        }

        // Montura A: Cara Y=0 (Sensor AS7341)
        cavidad_montura();

        // Montura B: Cara X=block_size (Placa LED a 90°)
        translate([block_size, 0, 0])
            rotate([0, 0, 90])
                cavidad_montura();
    }
}

// Cavidad de montaje para sensores y LED
module cavidad_montura() {
    translate([tube_pos_x, -1, optical_z])
        rotate([-90, 0, 0])
            cylinder(h = tube_pos_y + 1, d = pinhole_dia);

    translate([tube_pos_x - pcb_w/2, -0.1, optical_z - pcb_h/2])
        cube([pcb_w, pocket_depth + 0.1, pcb_h]);

    translate([tube_pos_x - (pcb_w + 3.5)/2, -0.1, optical_z - 3.5])
        cube([pcb_w + 3.5, pocket_depth + 0.1, 7.0]);

    translate([tube_pos_x - 9.0, -0.1, optical_z - pcb_h/2 - 2.0])
        cube([18.0, pocket_depth + 0.1, 4.0]);

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

// Case para el Arduino Mega 2560 (Ventanas cerradas con dintel superior)
module case_arduino_mega() {
    difference() {
        // Bloque exterior del case
        cube([case_outer_x, case_outer_y, case_inner_h + mega_floor]);

        // Hueco interior
        translate([mega_wall, mega_wall, mega_floor])
            cube([case_inner_x, case_inner_y, case_inner_h + 5]);

        // Ventana cerrada para Conector USB Tipo B
        translate([-1, mega_wall + clearance + 32.0, mega_floor + standoff_h])
            cube([mega_wall + 2, 13.0, 11.5]);

        // Ventana cerrada para Jack de Alimentación DC
        translate([-1, mega_wall + clearance + 4.0, mega_floor + standoff_h])
            cube([mega_wall + 2, 10.5, 11.0]);
    }

    // Torretas de fijación M3
    for (h = mega_holes) {
        translate([mega_wall + clearance + h[0], mega_wall + clearance + h[1], mega_floor]) {
            difference() {
                cylinder(h = standoff_h, d = standoff_od);
                translate([0, 0, -0.5])
                    cylinder(h = standoff_h + 1, d = standoff_id);
            }
        }
    }
}

// Auxiliar para redondeos
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