#!/bin/bash
# Script para buscar roles IAM existentes que puedan usarse para Lambda

echo "🔍 Buscando roles IAM existentes que puedan usarse para Lambda..."
echo ""

# Buscar roles que tengan Lambda en el nombre o en el trust policy
echo "Roles que contienen 'lambda' en el nombre:"
aws iam list-roles --query "Roles[?contains(RoleName, 'lambda') || contains(RoleName, 'Lambda')].{Name:RoleName, ARN:Arn}" --output table

echo ""
echo "Roles que permiten 'lambda.amazonaws.com' en el trust policy:"
aws iam list-roles --query "Roles[?AssumeRolePolicyDocument.Statement[?Principal.Service=='lambda.amazonaws.com']].{Name:RoleName, ARN:Arn}" --output table

echo ""
echo "Roles disponibles en tu cuenta:"
aws iam list-roles --query "Roles[].{Name:RoleName, ARN:Arn}" --output table | head -20

echo ""
echo "💡 Si encuentras un rol adecuado, cópialo y agrégalo a terraform.tfvars:"
echo "   lambda_role_arn = \"arn:aws:iam::TU_ACCOUNT_ID:role/NOMBRE_DEL_ROL\""

