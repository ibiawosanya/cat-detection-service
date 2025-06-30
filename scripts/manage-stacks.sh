#!/bin/bash
# manage-stacks.sh - Multi-environment stack management

echo "��� Cat Detector - Stack Management"
echo "=================================="

show_menu() {
    echo ""
    echo "Available operations:"
    echo "1. List all stacks"
    echo "2. Create new stack"
    echo "3. Switch stack"
    echo "4. Deploy current stack"
    echo "5. Show stack outputs"
    echo "6. Show stack configuration"
    echo "7. Set stack configuration"
    echo "8. Compare stacks"
    echo "9. Delete stack"
    echo "0. Exit"
    echo ""
}

list_stacks() {
    echo "��� Available stacks:"
    pulumi stack ls
    echo ""
    echo "Current stack: $(pulumi stack --show-name)"
}

create_stack() {
    read -p "Enter new stack name: " -r stack_name
    if [ -z "$stack_name" ]; then
        echo "❌ Stack name cannot be empty"
        return
    fi
    
    pulumi stack init "$stack_name"
    
    # Set default configuration based on stack name
    case $stack_name in
        prod*)
            pulumi config set aws:region eu-west-1
            pulumi config set cat-detector:environment prod
            pulumi config set cat-detector:lambda-memory 1024
            pulumi config set cat-detector:lambda-timeout 60
            ;;
        staging*)
            pulumi config set aws:region eu-west-1
            pulumi config set cat-detector:environment staging
            pulumi config set cat-detector:lambda-memory 768
            pulumi config set cat-detector:lambda-timeout 45
            ;;
        *)
            pulumi config set aws:region eu-west-1
            pulumi config set cat-detector:environment dev
            pulumi config set cat-detector:lambda-memory 512
            pulumi config set cat-detector:lambda-timeout 30
            ;;
    esac
    
    echo "✅ Stack '$stack_name' created and configured"
}

switch_stack() {
    echo "��� Available stacks:"
    pulumi stack ls
    echo ""
    read -p "Enter stack name to switch to: " -r stack_name
    if [ -z "$stack_name" ]; then
        echo "❌ Stack name cannot be empty"
        return
    fi
    
    pulumi stack select "$stack_name"
    echo "✅ Switched to stack: $stack_name"
}

deploy_stack() {
    current_stack=$(pulumi stack --show-name)
    echo "��� Deploying stack: $current_stack"
    echo ""
    
    pulumi preview
    echo ""
    read -p "Continue with deployment? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pulumi up
    else
        echo "Deployment cancelled"
    fi
}

show_outputs() {
    current_stack=$(pulumi stack --show-name)
    echo "��� Outputs for stack: $current_stack"
    pulumi stack output
}

show_config() {
    current_stack=$(pulumi stack --show-name)
    echo "⚙️  Configuration for stack: $current_stack"
    pulumi config
}

set_config() {
    echo "⚙️  Set configuration value"
    read -p "Enter config key: " -r config_key
    read -p "Enter config value: " -r config_value
    
    if [ -n "$config_key" ] && [ -n "$config_value" ]; then
        pulumi config set "$config_key" "$config_value"
        echo "✅ Set $config_key = $config_value"
    else
        echo "❌ Both key and value are required"
    fi
}

compare_stacks() {
    echo "��� Stack Comparison"
    pulumi stack ls
    echo ""
    read -p "Enter first stack name: " -r stack1
    read -p "Enter second stack name: " -r stack2
    
    if [ -z "$stack1" ] || [ -z "$stack2" ]; then
        echo "❌ Both stack names are required"
        return
    fi
    
    echo ""
    echo "Configuration comparison:"
    echo "========================"
    
    echo "Stack $stack1:"
    pulumi stack select "$stack1"
    pulumi config
    
    echo ""
    echo "Stack $stack2:"
    pulumi stack select "$stack2"
    pulumi config
}

delete_stack() {
    echo "��� Available stacks:"
    pulumi stack ls
    echo ""
    read -p "Enter stack name to delete: " -r stack_name
    if [ -z "$stack_name" ]; then
        echo "❌ Stack name cannot be empty"
        return
    fi
    
    echo "⚠️  This will permanently delete stack '$stack_name' and all its resources!"
    read -p "Are you absolutely sure? Type 'DELETE' to confirm: " -r confirmation
    
    if [ "$confirmation" = "DELETE" ]; then
        pulumi stack select "$stack_name"
        pulumi destroy --yes
        pulumi stack rm "$stack_name" --yes
        echo "✅ Stack '$stack_name' deleted"
    else
        echo "❌ Deletion cancelled"
    fi
}

# Main menu loop
while true; do
    show_menu
    read -p "Select operation (0-9): " -r choice
    
    case $choice in
        1) list_stacks ;;
        2) create_stack ;;
        3) switch_stack ;;
        4) deploy_stack ;;
        5) show_outputs ;;
        6) show_config ;;
        7) set_config ;;
        8) compare_stacks ;;
        9) delete_stack ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo "❌ Invalid option. Please select 0-9." ;;
    esac
done
