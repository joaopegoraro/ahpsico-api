## Tela de login:
- Numero de telefone;
- Verifica se existe conta com esse telefone, se existe mostra campo de código;
- Se não existe conta, mostra campo de código também, mas ao finalizar validação, pede 
se o usuário é paciente ou psicólogo, e mostra tela de criação de perfil;

## Tela home do psicólogo:
- Botão para ver pacientes -> abre tela de pacientes;
- Botão para ver dicas enviadas -> abre tela de dicas;
- Resumo da agenda -> abre tela de agenda;
- Sessões do dia, embaixo do resumo da agenda -> abre tela de sessão;
- FAB com botões para:
  - Adicionar paciente;
  - Mandar dica;

## Tela paciente:
- Botão para ver sessões -> abre tela de sessões;
- Botão para ver tarefas -> abre tela de tarefas;
- Botão para ver dicas -> abre tela de dicas;
- Próxima sessão -> abre tela de sessão;
- Tarefas pendentes -> abre tela de tarefa;

## Tela sessões:
- Lista de sessões, ordenadas por data -> abre tela de sessão;
- Item de sessão mostra o nome do psicólogo;
- Item de sessão mostra o status de confirmação;
- Item de sessão mostra o status do pagamento;
- Caso sessão seja mensal, item de sessão mostra qual sessão é do mês (Ex: "Sessão 2 de 4");

## Tela sessão:
- informação do psicólogo -> abre tela de perfil de psicólogo;
- Status do pagamento -> abre tela de pagamento;
- status de confirmação -> abre tela de confirmação;
- Caso sessão seja mensal, mostra qual sessão é do mês (Ex: "Sessão 2 de 4");

## Tela de confirmação (bottomsheet ou dialog?): 
- Botão para confirmar ou cancelar sessão;

## Tela de pagamento (bottom sheet ou dialog?):
- Dados do pix (chave pix), com botão de copiar;
- Dados bancários para transferência;

## Tela Dicas:
- Lista de dicas -> abre tela de dica;

## Tela dica (dialog ou bottomsheet?):
  - Modo de edição;
  - Escolher paciente para receber dica ou enviar para todos;
  - Campo de escrever mensagem;

## Tela adicionar paciente (dialog?):
  - Número de telefone;
  - checagem se paciente já existe, se já existe, mandar convite, senão, 
  criar link de criação de conta e gerar convite com número de telefone, para que paciente 
  quando criar conta já tenha o convite esperando confirmação;

## Tela home do paciente:
- Botão para ver sessões -> abre tela de sessões;
- Botão para ver tarefas -> abre tela de tarefas;
- Resumo da agenda -> abre tela de agenda;
- Próxima sessão, embaixo do resumo da agenda -> abre tela de sessão;
- Notificações:
  - Tarefas pendentes -> abre tela de tarefa;
  - Dicas -> abre tela de dica;

## Tela perfil do psicólogo:
- Foto;
- Nome;
- CRP;
- Descrição;

## Tela de agenda:
- Dias e sessões marcadas na agenda do psicologo;
- Dias e sessões marcadas na agenda do paciente;
- Botão para agendar sessão (paciente) -> abre tela de marcar sessão;
- Botão para bloquear horários (psicólogo) -> abre tela de marcar horário;
- Botão para ver sessões (paciente) -> abre tela de sessões;
- Botão para ver pacientes (psicólogo) -> abre tela de pacientes;

## Tela de marcar sessão:
- Escolher pagamento antecipado ou na hora;
- Escolher mensal ou indiviual;
- Escolher horário das sessões -> abrir tela de escolher horário;

## Tela de escolher horário:
- Para o psicológo, marcar horários que não estarão disponíveis;
- Para o paciente, marcar horário para marcar sessão;

## Tela de tarefas:
- Lista de tarefas do paciente, separadas por data de entrega;
- Clicar abre tela de tarefa;

## Tela de tarefa (bottom sheet?):
- Modo de edição (para criar ou editar tarefa);
- Nome da tarefa
- Sessão para entrega
- Lista de afazeres 
- Botão de marcar como concluído
