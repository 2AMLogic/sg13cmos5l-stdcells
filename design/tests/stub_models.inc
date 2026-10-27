* Logic-level stand-ins for the PDK sg13_lv_nmos / sg13_lv_pmos wrappers.
* NOT the PDK models: they only check connectivity and logic function.
* `w` is the total width (split over `ng` fingers); here it just scales M.
.model nstub nmos level=1 vto=0.4 kp=200u lambda=0.05
.model pstub pmos level=1 vto=-0.4 kp=80u lambda=0.05
.subckt sg13_lv_nmos d g s b w=1u l=0.13u ng=1 m=1
M1 d g s b nstub w={w} l={l} m={m}
.ends sg13_lv_nmos
.subckt sg13_lv_pmos d g s b w=1u l=0.13u ng=1 m=1
M1 d g s b pstub w={w} l={l} m={m}
.ends sg13_lv_pmos
