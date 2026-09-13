-- <target_schema>_<custome_schema>
-- <staging>_<marts>


-- It accepts two arguments:

-- custom_schema_name → schema specified in your model/config
-- node → information about the dbt model currently being processed

-- In your code, node isn't actually used.


{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- if custom_schema_name is none -%}
        {{ target.schema }}

    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}