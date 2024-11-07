from sympy import symbols, apart, degree, parse_expr
import schemdraw
import schemdraw.elements as elm
import sympy as sp 
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image

s = symbols('s')
st.title("Circuit Diagram Generator")
st.write("**Create Circuit Diagrams with Z(s) or Y(s)**")
# Custom CSS for styling
st.markdown("""
    <style>
    /* Main background color */
    body {
        background-color: #f5f7fa;
        color: #333;
        font-family: 'Arial', sans-serif;
    }

    /* Header styling */
    h1, h2, h3 {
        color: #4a4a4a;
        text-align: center;
    }

    /* Center the circuit image */
    .circuit-diagram {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }

    /* Style select boxes and text input */
    .stSelectbox, .stTextInput, .stButton {
        text-align: center;
        background-color: #e8e8e8;
        border: 1px solid #ccc;
        border-radius: 10px;
        padding: 8px;
        margin: 10px;
        font-size: 16px;
    }

    /* Style the warning, error, and info messages */
    .stAlert {
        background-color: #f1f1f1;
        color: #3a3a3a;
        border: 1px solid #b5b5b5;
        border-radius: 8px;
    }

    /* Pole-zero plot styling */
    .plot-container {
        margin: 20px auto;
        width: 80%;
        background-color: #fff;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

foster_type = st.selectbox("Select Foster form", ['1', '2'], help="Choose between Foster I or Foster II form.")
A_expr = st.text_input("Enter the numerator A(s):")
B_expr = st.text_input("Enter the denominator B(s):")
if A_expr and B_expr:  # Check if input is provided
    try:
        A = parse_expr(A_expr, {'s': s})
        B = parse_expr(B_expr, {'s': s})
    except SympifyError:
        st.error("Invalid mathematical expression. Please enter a valid polynomial in terms of s.")
else:
    st.warning("Please enter both the numerator A(s) and denominator B(s).")
# A = parse_expr(A_expr, {'s': s})
# B = parse_expr(B_expr, {'s': s})

if foster_type == '1':
    st.write("You selected Foster I form.")
    form =1 
    Z = A / B
elif foster_type == '2':
    st.write("You selected Foster II form.")
    form = 2
    Y = A/B
else:
    st.write("Invalid choice. Please select '1' or '2'.")
    exit()
y = 0
k = 0 
zeros = sp.solve(A, s)
st.write("zeroes",zeros)
poles = sp.solve(B, s)
st.write("poles",poles)
zeros = [complex(z) for z in zeros]
poles = [complex(p) for p in poles]

def rules_LC(A,B):
    c = 0
    zeros = sp.solve(A, s)
    poles = sp.solve(B, s)
    combined = [(z, 'zero') for z in zeros] + [(p, 'pole') for p in poles]
    combined.sort(key=lambda x: (sp.re(x[0]), sp.im(x[0])))
    has_zero = (0 in zeros) or (0 in poles)
    if has_zero:
        c += 1
    if degree(A)%2 ==0 and degree(B)%2 ==1 or degree(A)%2 ==1 and degree(B)%2 ==0:
        c += 1 
    if all(sp.re(z) == 0 for z in zeros + poles):
        c += 1

    for i in range(len(combined) - 1):
        if combined[i][1] == combined[i + 1][1]: 
            return c, 0
    return c, 1
count_LC, poles_alternate = rules_LC(A,B)
if poles_alternate == 1:
    count_LC += 1
if count_LC == 4:
    y=1
    st.write("CIRCUIT TYPE = LC circuit")

def rules_RC(A,B):
    c = 0
    zeros = sp.solve(A, s)
    poles = sp.solve(B, s)
    combine = [(z, 'zero') for z in zeros] + [(p, 'pole') for p in poles]
    combine.sort(key=lambda x: (sp.re(x[0]), sp.im(x[0])))
    if combine[len(combine) - 1][1]== 'pole':
        c += 1
    if all(sp.re(z) <= 0 and sp.im(z) == 0 for z in zeros + poles):
        c += 1
    for i in range(len(combine) - 1):
        if combine[i][1] == combine[i + 1][1]: 
            return c, 0
    return c, 1
count_RC, poles_1 = rules_RC(A,B)
if poles_1 == 1:
    count_RC += 1
if count_RC == 3:
    y=1
    if form ==1:
        st.write("CIRCUIT TYPE = RC Circuit")
    elif form == 2:
        st.write("CIRCUIT TYPE = RL Circuit")

def rules_RL(A,B):
    c = 0
    zeros = sp.solve(A, s)
    poles = sp.solve(B, s)
    combine = [(z, 'zero') for z in zeros] + [(p, 'pole') for p in poles]
    combine.sort(key=lambda x: (sp.re(x[0]), sp.im(x[0])))
    if combine[len(combine) - 1][1]=='zero':
        c += 1
    if all(sp.re(z) <= 0 and sp.im(z) == 0 for z in zeros + poles):
        c += 1
    # Check alternation
    for i in range(len(combine) - 1):
        if combine[i][1] == combine[i + 1][1]:
            return c, 0
    return c, 1
count_RL, poles_2 = rules_RL(A,B)
if poles_2 == 1:
    count_RL += 1
if count_RL == 3:
    y=1
    k=1
    if form == 1:
        st.write("CIRCUIT TYPE = RL Circuit")
    elif form == 2:
        st.write("CIRCUIT TYPE = RC Circuit")
if y!=1: 
    st.write("Neither LC, RL or RC")

def circuit_mapping_from_partial_fractions(W,k):
    with schemdraw.Drawing() as d:
        components = []
        updated = 0
        if k!=1:
            partial_fractions = apart(W)
            st.write("Partial fractions:", partial_fractions)
            x=0
        while True and k==1:
            partial_fractions = apart(W)
            st.write("Partial fractions:", partial_fractions)
            for term in partial_fractions.as_ordered_terms():
                num1 = term.as_numer_denom()[0]
                sub = num1.subs(s,0)
                if sub < 0 and updated==0:
                    st.write("Negative term found:", term)
                    W = W / s
                    updated += 1  
                    break  
            if updated == 1:
                updated +=1 
                x=1
                continue
            else:
                break
        for term in partial_fractions.as_ordered_terms():
            numerator = term.as_numer_denom()[0]
            denominator = term.as_numer_denom()[1]
            if x == 1 and k == 1 :
                if denominator.subs(s,0) == 0 and degree(denominator)==1:
                    constant_factor = denominator.coeff(s)
                    term = numerator / constant_factor
                    numerator = term.as_numer_denom()[0]
                    denominator = term.as_numer_denom()[1]
                else:
                    numerator = numerator*s
                    term = numerator/denominator
            if degree(denominator) == 0 and numerator.has(s):
                a = term.coeff(s)
                if form == 1:
                    components.append(f'Inductor of value {a}')
                    d += elm.Inductor().label(f"{a} H")
                elif form == 2:
                    components.append(f'Capacitor of value {a}')
                    d += elm.Line().right(2)
                    d += elm.Line().down(3)
                    d += elm.Capacitor().down().label(f"{a} F")
                    d += elm.Line().left(2)
                    d.move(2,6)
            
            elif denominator.subs(s, 0) == 0:
                constant_factor = denominator.coeff(s)
                a = numerator / constant_factor
                if form == 1:
                    components.append(f'Capacitor of value {1/a}')
                    d += elm.Capacitor().label(f"{1/a} F")
                elif form == 2:
                    components.append(f'Inductor of value {1/a}')
                    d += elm.Line().right(2)
                    d += elm.Line().down(3)
                    d += elm.Inductor().down().label(f"{1/a} H")
                    d += elm.Line().left(2)
                    d.move(2,6)

            elif degree(denominator) == 0 and degree(numerator)==0:
                if form == 1:
                    a = term
                    components.append(f'Resistor of value {a}')
                    d += elm.Resistor().label(f"{a} Ω")
                elif form == 2:
                    a = 1/term
                    components.append(f'Resistor of value {a}')
                    d += elm.Line().right(2)
                    d += elm.Line().down(3)
                    d += elm.Resistor().down().label(f"{a} Ω")
                    d += elm.Line().left(2)
                    d.move(2,6)

            elif degree(numerator)==0 and denominator.subs(s,0)!= 0 and degree(denominator)== 1:
                constant_factor = denominator.coeff(s)
                a = numerator / constant_factor
                b = (denominator/constant_factor) - s 
                if form == 1:
                    components.append(f'Capacitor of value {1/a} in parallel with Resistor of value {a/b}')
                    d += elm.Line().right(1) 
                    d += elm.Line().up(1)
                    d += elm.Capacitor().right(1.5).label(f"{1/a} F")
                    d += elm.Line().down(1)  
                    d += elm.Line().down(1)
                    d += elm.Resistor().left(1.5).label(f"{a/b} Ω")  
                    d += elm.Line().up(1)  
                    d.move(1.5,0)
                    d += elm.Line().right(1)
                elif form == 2:
                    components.append(f'Inductor of value {1/a} in parallel with Resistor of value {b/a}')
                    d += elm.Line().right(2)  
                    d += elm.Resistor().down().label(f"{b/a} Ω")
                    d += elm.Inductor().label(f"{1/a} H")
                    d += elm.Line().left(2)
                    d.move(2,6) 
                
            elif numerator.has(s) and degree(denominator)==1 :
                constant_factor = denominator.coeff(s)
                a = numerator.coeff(s) / constant_factor
                b = (denominator/constant_factor) - s
                if form ==1 :
                    components.append(f'Resistor of value {a} in parallel with Inductor of value {a/b}')
                    d += elm.Line().right(1)  
                    d += elm.Line().up(1)
                    d += elm.Inductor().right(1.5).label(f"{a/b} H")
                    d += elm.Line().down(1) 
                    d += elm.Line().down(1)
                    d += elm.Resistor().left(1.5).label(f"{a} Ω")  
                    d += elm.Line().up(1)  
                    d.move(1.5,0)
                    d += elm.Line().right(1)
                elif form == 2: 
                    components.append(f'Resistor of value {1/a} in parallel with Capacitor of value {a/b}')
                    d += elm.Line().right(2)  # Initial spacing
                    d += elm.Resistor().down().label(f"{1/a} Ω")
                    d += elm.Capacitor().label(f"{a/b} F")
                    d += elm.Line().left(2)
                    d.move(2,6)
               
            elif degree(numerator) == 1 and degree(denominator) == 2:
                constant_factor = denominator.coeff(s**2)
                a = numerator.coeff(s) / constant_factor
                b = (denominator/constant_factor) - s**2
                if form == 1:
                    components.append(f'Inductor of value {a/b} and Capacitor of value {1/a}')
                    d += elm.Line().right(1) 
                    d += elm.Line().up(1)
                    d += elm.Inductor().right(1.5).label(f"{a/b} H")
                    d += elm.Line().down(1) 
                    d += elm.Line().down(1)
                    d += elm.Capacitor().left(1.5).label(f"{1/a} F")  
                    d += elm.Line().up(1)  
                    d.move(1.5,0)
                    d += elm.Line().right(1)
                elif form == 2:
                    components.append(f'Inductor of value {1/a} and Capacitor of value {a/b}')
                    d += elm.Line().right(2) 
                    d += elm.Capacitor().down().label(f"{a/b} F")
                    d += elm.Inductor().label(f"{1/a} H")
                    d += elm.Line().left(2)
                    d.move(2,6)
        d.save('circuit_diagram.png')
    return components

if st.button("Generate Circuit"):
    if y==1 :
        st.markdown("<div class='circuit-diagram'>", unsafe_allow_html=True)
        circuit_image = Image.open('circuit_diagram.png')
        st.image(circuit_image, caption='Generated Circuit Diagram', use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if form == 1:
            components = circuit_mapping_from_partial_fractions(Z,k)
        if form == 2: 
            components = circuit_mapping_from_partial_fractions(Y,k)

if st.button("Show Pole-Zero Plot"):
    # Plotting Zeroes and poles 
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#bcebdd') 
    plt.axhline(0, color='black', linewidth=0.8)
    plt.axvline(0, color='black', linewidth=0.8)
    plt.grid(color='gray', linestyle='--', linewidth=0.6)

    # Plot zeros and poles with custom markers
    plt.scatter([z.real for z in zeros], [z.imag for z in zeros], color='royalblue', label='Zeros', marker='D', s=100, edgecolor='black')
    plt.scatter([p.real for p in poles], [p.imag for p in poles], color='darkorange', label='Poles', marker='*', s=150, edgecolor='black')
    plt.ylabel('Imaginary Part', fontsize=12, color='white')
    plt.title('Pole-Zero Plot', fontsize=14, color='white')
    plt.legend(fontsize=12, loc='upper right')
    ax.tick_params(axis='both', which='major', labelsize=10, colors="#151d3d")
    # plt.show()
    st.pyplot(fig)      
st.markdown("<style>.footer {position: fixed; bottom: 0; right =0; width: 100%; text-align: center; font-size: 0.9rem; color: #888;}</style>", unsafe_allow_html=True)
st.markdown("<div class='footer'>Circuit Diagram Generator - Created by Bhavani ( Roll Number - 108123024)</div>", unsafe_allow_html=True)  