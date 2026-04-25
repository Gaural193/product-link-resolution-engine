import typer
import json
import pandas as pd
from pathlib import Path
from db import init_db

app = typer.Typer(help="CLI tool to resolve product links for weekly deals.")

@app.command()
def setup_db():
    """Initialize the PostgreSQL database schema."""
    typer.echo("Initializing database schema...")
    try:
        init_db()
        typer.echo("Database initialized successfully.")
    except Exception as e:
        typer.echo(f"Error initializing database: {e}")

@app.command()
def enrich_links(input: str, output: str):
    """Process deals from JSON input and resolve links."""
    input_path = Path(input)
    output_path = Path(output)

    if not input_path.exists():
        typer.echo(f"Error: Input file {input} does not exist.")
        raise typer.Exit(code=1)

    typer.echo(f"Reading input from {input}...")
    
    # Placeholder for reading and processing the file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        typer.echo(f"Loaded {len(data)} rows.")

        from pipeline import PipelineManager
        pipeline = PipelineManager(source_name=input_path.name)
        enriched_data = pipeline.run(data)
        
        # Export to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=4)
            
        typer.echo(f"Results written to {output}.")
        
    except Exception as e:
        typer.echo(f"Error processing file: {e}")
        raise typer.Exit(code=1)

@app.command()
def generate_preview(input: str, output: str, retailer: str):
    """Generate an HTML email preview for a specific retailer."""
    input_path = Path(input)
    if not input_path.exists():
        typer.echo(f"Error: Input file {input} does not exist.")
        raise typer.Exit(code=1)
        
    from html_generator import generate_preview as gen_html
    
    success = gen_html(input, output, retailer)
    if success:
        typer.echo(f"HTML preview for {retailer} successfully generated at {output}!")
    else:
        typer.echo(f"Failed to generate preview. Are you sure {retailer} exists in the file?")

if __name__ == "__main__":
    app()
