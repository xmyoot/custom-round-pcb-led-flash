"""Project land patterns, transcribed from manufacturer drawings.

TPS63070: TI RNM0015A 4222000/B, example board layout page 40.
XFL4020: Coilcraft document 745-3 recommended land pattern.
Independent footprint checking is still a release gate.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'libraries'/'Round_LED_Flash.pretty'
OUT.mkdir(parents=True,exist_ok=True)

def header(name,desc):
    return [f'(footprint "{name}" (version 20260206) (generator "pcbnew") (layer "F.Cu") (descr "{desc}") (attr smd)',
            '(property "Reference" "REF**" (at 0 -3 0) (layer "F.SilkS") (effects (font (size .8 .8) (thickness .12))))',
            f'(property "Value" "{name}" (at 0 3 0) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12))))']

def pad(n,x,y,w,h,mask=.05):
    # Copper, paste and mask dimensions are explicit. Negative mask clearance
    # implements TI's solder-mask-defined power leads.
    return f'(pad "{n}" smd roundrect (at {x} {y}) (size {w} {h}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1) (solder_mask_margin {mask}))'

def rect(x1,y1,x2,y2,layer,width):
    return f'(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width {width}) (type default)) (fill none) (layer "{layer}"))'

def write(name,items):
    (OUT/(name+'.kicad_mod')).write_text('\n'.join(items+[')']))

name='TPS63070_RNM0015A'
s=header(name,'TI RNM0015A 4222000/B example land pattern. Power pads are mask defined. Datasheet page 40.')
for n,y in [(1,-.75),(2,-.25),(3,.25),(4,.75)]: s.append(pad(n,-1.15,y,.6,.25))
for n,x in [(5,-.725),(6,-.225),(14,-.225),(15,-.725)]: s.append(pad(n,x,1.4 if n<7 else -1.4,.25,.6))
for n,x,y in [(7,.275,1.4),(8,.775,1.4),(12,.775,-1.4),(13,.275,-1.4)]: s.append(pad(n,x,y,.25,.6,-.05))
# Wide joined lead-frame regions, with individual physical pin numbers retained.
s.append(pad(7,.525,1.15,.75,.6,-.05)); s.append(pad(13,.525,-1.15,.75,.6,-.05))
s.append(pad(9,.775,.5,1.35,.25,-.05))
s.append(pad(10,.6,0,1.7,.25,-.05))
s.append(pad(11,.775,-.5,1.35,.25,-.05))
s += [rect(-1.25,-1.5,1.25,1.5,'F.Fab',.1),rect(-1.75,-1.95,1.75,1.95,'F.CrtYd',.05),
      '(fp_circle (center -1.65 -.75) (end -1.55 -.75) (stroke (width .1) (type default)) (fill solid) (layer "F.SilkS"))']
write(name,s)

name='Coilcraft_XFL4020'
s=header(name,'Coilcraft XFL4020 document 745-3 land pattern; verify orientation of short/high-dv-dt lead at placement.')
for n,x in [(1,-1.675),(2,1.675)]: s.append(pad(n,x,0,.98,3.4))
s += [rect(-2,-2,2,2,'F.Fab',.1),rect(-2.4,-2.4,2.4,2.4,'F.CrtYd',.05)]
write(name,s)
print('Wrote TPS63070 and XFL4020 project footprints')
