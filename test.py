await query.message.delete()
await  query.message.answer('Бот ожидает перевода  на карту `4441114419894785` в течении 15 минут', parse_mode=ParseMode.MARKDOWN)

message_attributes = {
    'WorkerId': {
        'DataType': 'Number',
        'StringValue': f'{admin_chat_id}'
    },
    'MammonthId': {
        'DataType': 'Number',
        'StringValue': f'{query.message.from_user.id}'
    },
    'Sum': {
        'DataType': 'Number',
        'StringValue': f'{query.message.from_user.id}'
    }
}
sns.publish(TopicArn='arn:aws:sns:eu-north-1:441199499768:NewApplications',

            Message=f'''NewApplicationToTopUp''', MessageAttributes=message_attributes

            )
await waiting_for_mamont_async(datetime.datetime.now(), 0, 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc')

