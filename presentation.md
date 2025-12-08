<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crew Carbon Data Pipeline - Team Presentation</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css">
    <style>
        .reveal h1, .reveal h2, .reveal h3, .reveal h4, .reveal h5, .reveal h6 {
            text-transform: none;
        }
        .reveal {
            font-size: 32px;
        }
        .reveal pre {
            width: 100%;
            font-size: 0.55em;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        .reveal code {
            padding: 2px 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            align-items: center;
        }
        .highlight-box {
            background: rgba(102, 217, 239, 0.2);
            border-left: 4px solid #66d9ef;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 4px;
        }
        .stat-box {
            background: rgba(102, 217, 239, 0.15);
            padding: 1.5rem;
            margin: 0.5rem;
            border-radius: 8px;
            display: inline-block;
            min-width: 150px;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #66d9ef;
        }
        .stat-label {
            font-size: 0.8em;
            color: #999;
            margin-top: 0.5rem;
        }
        .tier {
            background: rgba(255,255,255,0.05);
            padding: 1rem;
            margin: 0.5rem;
            border-radius: 6px;
            border-left: 3px solid #66d9ef;
        }
        .tier-title {
            font-weight: bold;
            color: #66d9ef;
            margin-bottom: 0.5rem;
        }
        .tier-content {
            font-size: 0.85em;
            line-height: 1.6;
        }
        .validation-check {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        .validation-check:before {
            content: "✓ ";
            color: #a6e22e;
            font-weight: bold;
            margin-left: -1.5rem;
            margin-right: 0.5rem;
        }
        .center-content {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <!-- Title Slide -->
            <section class="center-content">
                <h1>🌱 Crew Carbon</h1>
                <h3>Data Pipeline Presentation</h3>
                <p style="margin-top: 2rem; color: #888;">CO₂ Removal Calculation & Data Management</p>
                <p style="margin-top: 3rem; font-size: 0.7em; color: #666;">By Abdel Alfahham</p>
            </section>

            <!-- What is Crew Carbon? -->
            <section>
                <h2>What Are We Building?</h2>
                <div class="highlight-box">
                    <p><strong>A data pipeline that:</strong></p>
                    <ul>
                        <li>📊 Ingests lab and operational data from wastewater treatment plants</li>
                        <li>🧪 Validates and transforms raw data</li>
                        <li>🧮 Calculates CO₂ removal using scientific formulas</li>
                        <li>📈 Visualizes results for stakeholders</li>
                    </ul>
                </div>
            </section>

            <!-- Architecture Overview -->
            <section>
                <h2>Three-Layer Architecture</h2>
                <div class="tier">
                    <div class="tier-title">Layer 1: Data Ingestion</div>
                    <div class="tier-content">Raw CSV/Excel files from plants → Upload to S3</div>
                </div>
                <div class="tier">
                    <div class="tier-title">Layer 2: Transformation</div>
                    <div class="tier-content">Clean & standardize → PostgreSQL normalized tables</div>
                </div>
                <div class="tier">
                    <div class="tier-title">Layer 3: Analysis & MRV</div>
                    <div class="tier-content">CO₂ calculations → Streamlit dashboard → Expert review</div>
                </div>
            </section>

            <!-- Services -->
            <section>
                <h2>Services We Run</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; font-size: 0.9em;">
                    <div class="highlight-box">
                        <strong>🐍 Python App</strong><br/>
                        Backend processing<br/>
                        <code>localhost:8500</code>
                    </div>
                    <div class="highlight-box">
                        <strong>🐘 PostgreSQL</strong><br/>
                        Normalized data<br/>
                        <code>crewcarbon:localdev@postgres</code>
                    </div>
                    <div class="highlight-box">
                        <strong>📊 Streamlit</strong><br/>
                        Interactive dashboard<br/>
                        <code>http://0.0.0.0:8501</code>
                    </div>
                    <div class="highlight-box">
                        <strong>📓 Jupyter</strong><br/>
                        Data exploration<br/>
                        <code>http://localhost:8888</code>
                    </div>
                </div>
            </section>

            <!-- Quick Start -->
            <section>
                <h2>Getting Started (30 seconds)</h2>
                <pre><code class="language-bash"># 1. Build containers
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Initialize & run pipelines
make run-all-pipelines

# 4. Open dashboard
# Streamlit: http://0.0.0.0:8501/
# Jupyter: http://localhost:8888/</code></pre>
            </section>

            <!-- Data Pipelines -->
            <section>
                <h2>Data Transformation Pipelines</h2>
                <p style="text-align: left; font-size: 0.9em;">
                    <strong>All follow the same pattern:</strong>
                </p>
                <pre><code>Load → Transform → Compress Metadata → Insert to DB</code></pre>
            </section>

            <!-- Calcium Pipeline -->
            <section>
                <h3>Calcium (Ca) Pipeline</h3>
                <div class="highlight-box">
                    <p><strong>Input:</strong> Lab data CSV files</p>
                    <p><strong>Output:</strong> <code>crew_carbon_lab_reading</code> table</p>
                    <p><strong>Processing:</strong></p>
                    <ul style="font-size: 0.85em;">
                        <li>Select Ca²⁺ columns</li>
                        <li>Rename to schema</li>
                        <li>Convert types (string → FLOAT)</li>
                        <li>Compress extra metadata as JSON</li>
                    </ul>
                </div>
            </section>

            <!-- pH Pipeline -->
            <section>
                <h3>pH Sensor Pipeline</h3>
                <div class="highlight-box">
                    <p><strong>Input:</strong> 2 CSV files (minute-by-minute readings)</p>
                    <p><strong>Output:</strong> <code>crew_carbon_lab_reading</code> table</p>
                    <p><strong>Key Difference:</strong></p>
                    <ul style="font-size: 0.85em;">
                        <li>Combines multiple sensor files</li>
                        <li>Higher frequency (minute-level)</li>
                        <li>Same standardization as Calcium</li>
                    </ul>
                </div>
            </section>

            <!-- Operations Pipelines -->
            <section>
                <h2>Operations Data Pipelines</h2>
                <div class="two-column" style="font-size: 0.85em;">
                    <div class="highlight-box">
                        <p><strong>Plant A Ops</strong></p>
                        <ul>
                            <li>3 Excel files (Apr-Jun)</li>
                            <li>Effluent flow</li>
                            <li>Bypass metrics</li>
                        </ul>
                    </div>
                    <div class="highlight-box">
                        <p><strong>Plant B Ops</strong></p>
                        <ul>
                            <li>6 Excel files (Mar-Jul)</li>
                            <li>Multi-level headers</li>
                            <li>Flow metrics only</li>
                        </ul>
                    </div>
                </div>
                <p style="margin-top: 1rem; font-size: 0.85em; text-align: center;">Both output to: <code>waste_water_plant_operation</code></p>
            </section>

            <!-- CO2 Calculation: Step 1 -->
            <section>
                <h2>CO₂ Removal Calculation</h2>
                <h4>Step 1: Calcium Delta</h4>
                <pre><code class="language-python">ca_delta = ca_downstream - ca_upstream  # mg/L</code></pre>
                <p style="font-size: 0.85em; margin-top: 1rem;">This tells us how much calcium was removed</p>
            </section>

            <!-- CO2 Calculation: Step 2-3 -->
            <section>
                <h4>Step 2-3: Flow Rate & CaCO₃ Mass</h4>
                <pre><code class="language-python">flow_mgd = operational_data.actual_eff_flow_mgd
flow_l_day = flow_mgd * 3785.41 * 1000

ca_to_caco3 = 100.0869 / 40.078  # Molecular ratio
caco3_mg = ca_delta * flow_l_day * ca_to_caco3</code></pre>
            </section>

            <!-- CO2 Calculation: Step 4-5 -->
            <section>
                <h4>Step 4-5: CO₂ Mass & Final Conversion</h4>
                <pre><code class="language-python">co2_to_caco3 = 44.0095 / 100.0869  # MW_CO2 / MW_CaCO3
co2_mg = caco3_mg * co2_to_caco3

# Convert to MT/day (final result)
co2_mt_day = co2_mg / 1_000_000_000</code></pre>
            </section>

            <!-- Molecular Weights -->
            <section>
                <h2>Molecular Weights</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-top: 2rem;">
                    <div class="stat-box">
                        <div class="stat-value">40.078</div>
                        <div class="stat-label">MW_Ca (g/mol)</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">100.09</div>
                        <div class="stat-label">MW_CaCO₃ (g/mol)</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">44.01</div>
                        <div class="stat-label">MW_CO₂ (g/mol)</div>
                    </div>
                </div>
                <p style="margin-top: 2rem; font-size: 0.85em; text-align: center; color: #888;">These are used to convert calcium measurements to CO₂ removal</p>
            </section>

            <!-- QA/QC Validation -->
            <section>
                <h2>QA/QC: 5-Level Pyramid</h2>
                <div style="font-size: 0.8em; text-align: left;">
                    <div class="tier">
                        <div class="tier-title">Level 1: Raw Data Ingestion</div>
                        <div class="tier-content">File format, encoding, parsing, duplicates</div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Level 2: Data Completeness</div>
                        <div class="tier-content">Non-null columns, missing values, date records</div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Level 3: Schema & Type Validation</div>
                        <div class="tier-content">Data types, required fields, numeric ranges, FK integrity</div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Level 4: Data Quality Flags</div>
                        <div class="tier-content">Ca delta passed, flow checks passed</div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Level 5: Business Logic</div>
                        <div class="tier-content">MRV calculations correct, domain rules applied, expert review</div>
                    </div>
                </div>
            </section>

            <!-- MRV Validation Checks -->
            <section>
                <h2>MRV Validation Checks</h2>
                <div class="highlight-box" style="text-align: left;">
                    <div class="validation-check"><strong>Operational Data:</strong> Flow rates > 0</div>
                    <div class="validation-check"><strong>Calcium Readings:</strong> Both upstream & downstream exist</div>
                    <div class="validation-check"><strong>Calcium Delta:</strong> Must be > 0 (CO₂ removal detected)</div>
                </div>
                <div style="margin-top: 1.5rem; background: rgba(166, 226, 46, 0.15); padding: 1rem; border-left: 3px solid #a6e22e; border-radius: 4px;">
                    <p style="font-size: 0.85em;"><strong>Outcome:</strong> Critical failures stop calculation. Non-critical issues proceed but are flagged for review.</p>
                </div>
            </section>

            <!-- Database Schema -->
            <section>
                <h2>Core Database Tables</h2>
                <div style="font-size: 0.75em; text-align: left; display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="highlight-box">
                        <p><strong>surveys</strong></p>
                        <ul style="margin: 0.5rem 0; padding-left: 1rem;">
                            <li>id (PK)</li>
                            <li>survey_id (UNIQUE)</li>
                            <li>datum, projection</li>
                            <li>operator_name</li>
                            <li>peak_current_amps</li>
                        </ul>
                    </div>
                    <div class="highlight-box">
                        <p><strong>crew_carbon_lab_reading</strong></p>
                        <ul style="margin: 0.5rem 0; padding-left: 1rem;">
                            <li>id (PK)</li>
                            <li>plant_id (FK)</li>
                            <li>reading_date</li>
                            <li>parameter (Ca, pH)</li>
                            <li>value, unit, metadata</li>
                        </ul>
                    </div>
                    <div class="highlight-box">
                        <p><strong>waste_water_plant_operation</strong></p>
                        <ul style="margin: 0.5rem 0; padding-left: 1rem;">
                            <li>id (PK)</li>
                            <li>plant_id (FK)</li>
                            <li>operation_date</li>
                            <li>actual_eff_flow_mgd</li>
                            <li>bypass_flag, metadata</li>
                        </ul>
                    </div>
                    <div class="highlight-box">
                        <p><strong>co2_removal_calculation</strong></p>
                        <ul style="margin: 0.5rem 0; padding-left: 1rem;">
                            <li>ca_upstream_id (FK)</li>
                            <li>ca_downstream_id (FK)</li>
                            <li>ca_delta_mg_l</li>
                            <li>co2_mt_day</li>
                            <li>quality_flag, confidence</li>
                        </ul>
                    </div>
                </div>
            </section>

            <!-- Development Workflow -->
            <section>
                <h2>Development Workflow</h2>
                <div class="highlight-box">
                    <ol style="font-size: 0.9em; text-align: left;">
                        <li><strong>Local Dev:</strong> <code>make up</code> → Run pipelines locally</li>
                        <li><strong>View Data:</strong> <code>make db-shell</code> → Query PostgreSQL</li>
                        <li><strong>Jupyter:</strong> <code>http://localhost:8888</code> → Exploratory analysis</li>
                        <li><strong>Dashboard:</strong> <code>http://0.0.0.0:8501</code> → Test visualizations</li>
                        <li><strong>Reset:</strong> <code>make clean && make run-all-pipelines</code> → Full reset</li>
                    </ol>
                </div>
            </section>

            <!-- Common Make Commands -->
            <section>
                <h2>Essential Commands</h2>
                <pre><code>make up                  # Start containers
make down                # Stop containers
make shell               # Bash in app container
make db-shell            # PostgreSQL CLI
make test                # Run pytest
make clean               # Reset everything
make run-all-pipelines   # Full pipeline run</code></pre>
            </section>

            <!-- Statistics -->
            <section>
                <h2>Scale & Performance</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin: 2rem 0;">
                    <div class="stat-box">
                        <div class="stat-value">50-200</div>
                        <div class="stat-label">Receiver Stations</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">150-600</div>
                        <div class="stat-label">EM Responses</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">1,950-7,800</div>
                        <div class="stat-label">Off-Time Channels</div>
                    </div>
                </div>
                <p style="font-size: 0.85em; color: #888;">Per survey: 2,100-8,600+ total rows</p>
            </section>

            <!-- Team Roles -->
            <section>
                <h2>Who Does What?</h2>
                <div style="font-size: 0.8em; text-align: left;">
                    <div class="highlight-box">
                        <p><strong>👨‍💻 Data Engineers</strong><br/>Full dev access, write/test pipelines locally</p>
                    </div>
                    <div class="highlight-box">
                        <p><strong>🔬 Data Scientists</strong><br/>Read-only DB access, Jupyter notebooks, dashboards</p>
                    </div>
                    <div class="highlight-box">
                        <p><strong>👨‍🔬 Domain Experts</strong><br/>Dashboard review, approve/reject calculations</p>
                    </div>
                    <div class="highlight-box">
                        <p><strong>📊 Stakeholders</strong><br/>View KPIs & trends, no technical access</p>
                    </div>
                </div>
            </section>

            <!-- Architecture Diagram Explanation -->
            <section>
                <h2>End-to-End Data Flow</h2>
                <div class="highlight-box" style="font-size: 0.8em; text-align: left; line-height: 1.8;">
                    <p>📁 Raw Data Files</p>
                    <p>↓ Upload to S3</p>
                    <p>🔄 Parallel Pipelines (Ca, pH, Ops)</p>
                    <p>↓ Normalize to DB Tables</p>
                    <p>✅ QA/QC Validation (5 levels)</p>
                    <p>↓ Dashboard Visualization</p>
                    <p>👁️ Expert Review</p>
                    <p>↓ Final Approval</p>
                    <p>📈 Production Results</p>
                </div>
            </section>

            <!-- Performance Tips -->
            <section>
                <h2>Performance Best Practices</h2>
                <div class="highlight-box">
                    <p><strong>Database:</strong> Create indexes on frequently queried columns (plant_id, date)</p>
                </div>
                <div class="highlight-box">
                    <p><strong>Dashboard:</strong> Use Streamlit caching with <code>@st.cache_data</code></p>
                </div>
                <div class="highlight-box">
                    <p><strong>Data Ops:</strong> Batch inserts instead of one-by-one</p>
                </div>
                <div class="highlight-box">
                    <p><strong>Monitoring:</strong> CloudWatch tracks query times and slow queries</p>
                </div>
            </section>

            <!-- Troubleshooting -->
            <section>
                <h2>Quick Troubleshooting</h2>
                <div style="font-size: 0.75em; text-align: left;">
                    <div class="tier">
                        <div class="tier-title">Container won't start</div>
                        <div class="tier-content"><code>docker-compose logs app</code></div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">DB connection refused</div>
                        <div class="tier-content"><code>make db-shell</code> → Check PostgreSQL is running</div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Pipeline hangs</div>
                        <div class="tier-content"><code>docker-compose restart app</code></div>
                    </div>
                    <div class="tier">
                        <div class="tier-title">Dashboard shows no data</div>
                        <div class="tier-content">Run <code>make run-all-pipelines</code> to populate</div>
                    </div>
                </div>
            </section>

            <!-- Adding New Data Sources -->
            <section>
                <h2>Adding New Data Sources</h2>
                <div class="highlight-box" style="text-align: left;">
                    <ol style="font-size: 0.9em;">
                        <li>Create pipeline: <code>src/ingest/new_source_pipeline.py</code></li>
                        <li>Follow standardization pattern (Load → Transform → Compress → DB)</li>
                        <li>Update <code>run_data_pipeline.py</code></li>
                        <li>Write tests: <code>tests/test_new_source.py</code></li>
                        <li>Validate with <code>make test</code></li>
                    </ol>
                </div>
            </section>

            <!-- Cloud Deployment -->
            <section>
                <h2>Scalability & Cloud</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; font-size: 0.85em;">
                    <div class="highlight-box">
                        <p><strong>Storage:</strong> AWS S3 (raw data)</p>
                        <p><strong>Database:</strong> RDS PostgreSQL</p>
                        <p><strong>Compute:</strong> ECS containers</p>
                    </div>
                    <div class="highlight-box">
                        <p><strong>Scaling:</strong> Auto-scaling on traffic</p>
                        <p><strong>Backups:</strong> Multi-region replication</p>
                        <p><strong>Monitoring:</strong> CloudWatch + Datadog</p>
                    </div>
                </div>
            </section>

            <!-- Next Steps -->
            <section>
                <h2>Next Steps</h2>
                <div class="highlight-box">
                    <ol style="font-size: 0.95em;">
                        <li>✅ Run <code>make run-all-pipelines</code> locally</li>
                        <li>✅ Explore dashboard at <code>http://0.0.0.0:8501</code></li>
                        <li>✅ Review test suite with <code>make test</code></li>
                        <li>✅ Try Jupyter at <code>http://localhost:8888</code></li>
                        <li>✅ Join code review process</li>
                    </ol>
                </div>
            </section>

            <!-- Resources -->
            <section>
                <h2>Resources & Documentation</h2>
                <div style="font-size: 0.85em; text-align: left;">
                    <p>📚 <strong>Docker:</strong> https://docs.docker.com/</p>
                    <p>🐘 <strong>PostgreSQL:</strong> https://www.postgresql.org/docs/</p>
                    <p>🐍 <strong>SQLAlchemy:</strong> https://docs.sqlalchemy.org/</p>
                    <p>📊 <strong>Streamlit:</strong> https://docs.streamlit.io/</p>
                    <p>🐼 <strong>Pandas:</strong> https://pandas.pydata.org/docs/</p>
                    <p>📖 <strong>Full README:</strong> Check GitHub repository</p>
                </div>
            </section>

            <!-- Final Slide -->
            <section class="center-content">
                <h2>Questions?</h2>
                <div class="highlight-box" style="margin-top: 2rem;">
                    <p><strong>Crew Carbon Team</strong></p>
                    <p style="font-size: 0.85em; color: #888;">Abdel Alfahham</p>
                    <p style="font-size: 0.8em; margin-top: 1rem; color: #666;">2025 Data Pipeline Deck</p>
                </div>
            </section>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/plugin/notes/notes.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/plugin/highlight/highlight.min.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            transition: 'slide',
            transitionSpeed: 'default',
            width: 1000,
            height: 700,
            margin: 0.1,
            minScale: 0.2,
            maxScale: 2.0,
            plugins: [RevealHighlight],
            keyboard: true,
            touch: true,
        });
    </script>
</body>
</html>