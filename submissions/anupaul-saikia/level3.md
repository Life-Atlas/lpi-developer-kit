# Level 3 Submission — Track D: 3D & Visualization
## Anupaul Saikia | GitHub: Saikia05

Deliverables (also present in the external repo as file or link):

Project Link -> https://drive.google.com/drive/folders/1lL1tW7kZAnEFQINzHvIbh2cY8C4nHWQb
---

Walkthrough Video Link -> https://jumpshare.com/share/ehzXqNyyiKNQxFtWWtXF
---

## Project: (MADE IN BLENDER) 3D Twin of a mock wind tunnel to replicate air-flow of any collidable object.

A 3D (.blend/.fbx) replica of a conventiona wind tunnel with 'impact-zone-color-changing' - particles constituting air in a non-turbulant environment.


### Project Briefing:

1. The Emitter shoots random particles representing and mimicking airflow.
2. The object (given that it has collision physics - on) will deflect airflow to represent it aerodynamic characteristics.
3. Using <"Inputvalue"(velocity,time,frame,angle,etc)-to-valuetostring-to-stringtocurve-to-curvetomesh> Geometry node workflow to show values as 3D-UI
4. https://jumpshare.com/share/ehzXqNyyiKNQxFtWWtXF

#prerequisites -> Blender 4.0+

https://jumpshare.com/share/ehzXqNyyiKNQxFtWWtXF

-> set the viewport render preview from CYCLES to WORKBENCH
## Why this Idea?
> It was a path of my learning curve in 3D Generalism that involves everything that the CAD world provides.

## Repository Link:
https://github.com/Saikia05/MockWindTunnel3DTwin

# Agent (for extended software supports):

Here is an agent that converts .blend file to .fbx for other CAD/M software supports:


**'B2FBX.py'**

## How it works:

1. You type a conversational request to the LLM agent about what you want converted.
2. The LangChain AI decides to trigger the integrated python conversion tool.
3. The script scans your host machine to locate and validate the target `.blend` files.
4. For each file, it fires up a hidden, headless instance of the Blender engine in the background.
5. The exact same script detects it is now inside Blender (`bpy` mode) and switches its personality.
6. It precisely selects geometry, bakes scale, drops cameras, and applies modifiers for strict CAD compatibility.
7. The `.fbx` file saves, Blender closes, and the tool returns a success string back to the AI, which summarizes it for you!


## Example Query:

> Hey there! Can you dive into my "C:\MyGame\Assets" folder, grab all the raw blender files you can find, and put the CAD versions into "C:\MyGame\Exports"?

## Query Respones:

> Entering new AgentExecutor chain...
Invoking: `convert_blend_models` with `{'directory_path': 'C:\\MyGame\\Assets', 'output_directory': 'C:\\MyGame\\Exports'}`
[*] Processing: C:\MyGame\Assets\sword_hero.blend
[+] Successfully converted to: C:\MyGame\Exports\sword_hero.fbx
[*] Processing: C:\MyGame\Assets\shield_hero.blend
[+] Successfully converted to: C:\MyGame\Exports\shield_hero.fbx
[*] Processing: C:\MyGame\Assets\broken_file.blend
    [!] Skipping broken_file.blend due to error: Invalid input file: C:\MyGame\Assets\broken_file.blend
[*] Batch conversion finished. Converted 2/3 files.





---------
# LPI Tools Used
                                                | `smile_overview` | Get full SMILE methodology framework | Yes |
                                                | `query_knowledge` | Search knowledge base for domain-specific entries | Yes |
                                            

**Minimum 2 tools queried** — `smile_overview` + `query_knowledge` are always called;

## Query Used:
Prompt:
what is S.M.I.L.E.

## Query Response:
Used lpi-sandbox integration
Used lpi-sandbox integration
S.M.I.L.E. stands for Sustainable Methodology for Impact Lifecycle Enablement — it's a structured, benefits-driven framework for implementing digital twins across any industry, at any scale. The core philosophy can be summed up in one line:

"Absorb the past, simulate the future, to transcend the now."

What makes SMILE distinctive is its radical reversal of the conventional approach. Most organizations start by collecting data and then figure out what to do with it. SMILE does the opposite — start with the impact you want to achieve, then work backwards to identify what data you actually need.
